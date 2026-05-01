"""
Universal Indian Bank Statement Parser
Supports: CSV, XLSX, XLS, PDF
Banks: ICICI, HDFC, SBI, Kotak, Canara, KVB, Axis, and any standard format
"""

import re
import io
import pandas as pd


# ── Column keyword maps ─────────────────────────────────────────────────────

DATE_KW    = ['value date', 'value dt', 'txn date', 'transaction date',
               'trans. date', 'trans date', 'posting date', 'date']
DESC_KW    = ['description', 'narration', 'particulars', 'remarks',
               'transaction details', 'details', 'transaction remarks',
               'transaction description', 'chq desc', 'narrative']
DEBIT_KW   = ['withdrawal amt', 'withdrawal amount', 'withdrawals',
               'debit amount', 'debit amt', 'debit', 'dr amount', 'dr amt']
CREDIT_KW  = ['deposit amt', 'deposit amount', 'deposits',
               'credit amount', 'credit amt', 'credit', 'cr amount', 'cr amt']
AMOUNT_KW  = ['amount', 'amt', 'transaction amount']
DRCR_KW    = ['dr / cr', 'dr/cr', 'cr/dr', 'transaction type',
               'txn type', 'type', 'debit/credit']
BALANCE_KW = ['balance', 'closing balance', 'running balance', 'avail bal']


# ── Helper: fuzzy column finder ──────────────────────────────────────────────

def _find_col(columns, keywords):
    """Return first column whose lowercased name contains any keyword (longest match first)."""
    cols_lower = [str(c).lower().strip() for c in columns]
    # Sort keywords by length descending so longer (more specific) keywords win
    for kw in sorted(keywords, key=len, reverse=True):
        for i, col in enumerate(cols_lower):
            if kw in col:
                return columns[i]
    return None


def _clean_num(val):
    """Convert bank-formatted number string to float."""
    s = str(val).strip().replace(',', '').replace(' ', '')
    if s in ('', '-', '--', 'nan', 'None', 'N/A', 'n/a'):
        return 0.0
    s = re.sub(r'[^\d.]', '', s)
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


# ── Core normalizer ──────────────────────────────────────────────────────────

def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Given a raw DataFrame with any bank's column names,
    return a normalized DataFrame with:
      [Transaction Date, Description, Amount, Transaction Type (CR/DR)]
    """
    cols = list(df.columns)

    date_col   = _find_col(cols, DATE_KW)
    desc_col   = _find_col(cols, DESC_KW)
    debit_col  = _find_col(cols, DEBIT_KW)
    credit_col = _find_col(cols, CREDIT_KW)
    amount_col = _find_col(cols, AMOUNT_KW)
    drcr_col   = _find_col(cols, DRCR_KW)

    if not desc_col:
        # Last-resort: pick the column with the longest average string length
        text_cols = df.select_dtypes(include='object').columns.tolist()
        if text_cols:
            desc_col = max(text_cols,
                           key=lambda c: df[c].astype(str).str.len().mean())

    result = pd.DataFrame()

    # ── Date ────────────────────────────────────────────────────────────────
    if date_col:
        result['Transaction Date'] = pd.to_datetime(
            df[date_col], dayfirst=True, errors='coerce'
        )
    else:
        result['Transaction Date'] = pd.NaT

    # ── Description ─────────────────────────────────────────────────────────
    result['Description'] = df[desc_col].astype(str).str.strip() if desc_col else ''

    # ── Pattern A: Single Amount + DR/CR column (KVB, Axis-old, etc.) ───────
    if amount_col and drcr_col:
        result['Amount'] = df[amount_col].apply(_clean_num)
        result['Transaction Type'] = (
            df[drcr_col].astype(str).str.strip().str.upper()
        )

    # ── Pattern B: Separate Debit / Credit columns (HDFC, ICICI, SBI, etc.) ─
    elif debit_col and credit_col:
        dr_vals = df[debit_col].apply(_clean_num)
        cr_vals = df[credit_col].apply(_clean_num)
        amounts, types = [], []
        for dr, cr in zip(dr_vals, cr_vals):
            if cr > 0:
                amounts.append(cr);  types.append('CR')
            elif dr > 0:
                amounts.append(dr);  types.append('DR')
            else:
                amounts.append(0.0); types.append('CR')
        result['Amount'] = amounts
        result['Transaction Type'] = types

    # ── Pattern C: Only one amount-like column + no DR/CR ───────────────────
    elif amount_col:
        result['Amount'] = df[amount_col].apply(_clean_num)
        result['Transaction Type'] = 'CR'   # fallback

    else:
        return pd.DataFrame()   # cannot parse

    # ── Month helper ─────────────────────────────────────────────────────────
    if not result['Transaction Date'].isna().all():
        result['Month'] = result['Transaction Date'].dt.strftime('%Y-%m')
    else:
        result['Month'] = 'Unknown'
    result['Month'] = result['Month'].fillna('Unknown')

    # ── Clean up ─────────────────────────────────────────────────────────────
    result = result[result['Amount'] > 0]
    result = result[result['Description'].str.strip().str.lower().isin(['', 'nan']) == False]
    result = result.reset_index(drop=True)
    return result


# ── Row-skip finder (banks dump account info before the table) ───────────────

def _find_header_row(df: pd.DataFrame) -> pd.DataFrame:
    """
    Scan rows top-down; when we hit a row that looks like a header
    (contains a date keyword and a description keyword), restart from there.
    """
    for i in range(min(25, len(df))):
        row_str = ' '.join(str(v).lower() for v in df.iloc[i].values)
        has_date = any(k in row_str for k in ['date', 'txn', 'posting'])
        has_desc = any(k in row_str for k in ['description', 'narration',
                                               'particulars', 'details'])
        if has_date and has_desc:
            new_df = df.iloc[i + 1:].copy()
            new_df.columns = [str(v).strip() for v in df.iloc[i].values]
            return new_df.reset_index(drop=True)
    return df


# ── PDF reader ───────────────────────────────────────────────────────────────

def _read_pdf(file, password: str = '') -> tuple:
    """Extract tables from a PDF using pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        return None, "pdfplumber not installed. Run: pip install pdfplumber"

    try:
        open_kwargs = {'password': password} if password else {}
        all_rows, header = [], None

        with pdfplumber.open(file, **open_kwargs) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if not table:
                    continue
                # First non-None row as header
                if header is None:
                    header = [str(c).strip() if c else f'col_{i}'
                              for i, c in enumerate(table[0])]
                    all_rows.extend(table[1:])
                else:
                    # Skip repeated headers (printed on every page by some banks)
                    start = 1 if [str(c).strip() for c in table[0]] == header else 0
                    all_rows.extend(table[start:])

        if not header or not all_rows:
            return None, "No tabular data found in PDF. The PDF may be image-based (scanned)."

        df = pd.DataFrame(all_rows, columns=header)
        df.columns = df.columns.str.strip()
        # Drop fully empty rows
        df.dropna(how='all', inplace=True)
        return df, None

    except Exception as exc:
        return None, f"PDF read error: {exc}"


# ── Excel reader ─────────────────────────────────────────────────────────────

def _read_excel(file) -> tuple:
    try:
        xl = pd.ExcelFile(file, engine='openpyxl')
        best_df, best_rows = None, 0
        for sheet in xl.sheet_names:
            df = xl.parse(sheet, header=None, dtype=str)
            if len(df) > best_rows:
                best_rows = len(df)
                best_df = df
        if best_df is None:
            return None, "Excel file appears to be empty."
        return _find_header_row(best_df.copy()), None
    except Exception as exc:
        return None, f"Excel read error: {exc}"


def _read_xls(file) -> tuple:
    try:
        xl = pd.ExcelFile(file, engine='xlrd')
        best_df, best_rows = None, 0
        for sheet in xl.sheet_names:
            df = xl.parse(sheet, header=None, dtype=str)
            if len(df) > best_rows:
                best_rows = len(df)
                best_df = df
        if best_df is None:
            return None, "XLS file appears to be empty."
        return _find_header_row(best_df.copy()), None
    except Exception as exc:
        return None, f"XLS read error: {exc}"


# ── CSV reader ───────────────────────────────────────────────────────────────

def _read_csv(file) -> tuple:
    """
    Smart CSV reader: tries multiple encodings and skip-row values
    to locate the real header row.
    """
    encodings = ['utf-8', 'latin-1', 'cp1252']
    DATE_HINTS = ['date', 'txn', 'posting', 'value']
    DESC_HINTS = ['description', 'narration', 'particulars', 'details']

    raw_content = None
    if hasattr(file, 'read'):
        raw_content = file.read()
        if isinstance(raw_content, bytes):
            raw_content = raw_content.decode('utf-8', errors='replace')

    def try_parse(content_or_path, skip):
        for enc in encodings:
            try:
                if isinstance(content_or_path, str) and '\n' in content_or_path:
                    buf = io.StringIO(content_or_path)
                    df = pd.read_csv(buf, skiprows=skip, dtype=str, encoding=enc,
                                     on_bad_lines='skip')
                else:
                    df = pd.read_csv(content_or_path, skiprows=skip, dtype=str,
                                     encoding=enc, on_bad_lines='skip')
                return df
            except Exception:
                continue
        return None

    source = raw_content if raw_content else file

    for skip in range(0, 20):
        df = try_parse(source, skip)
        if df is None or df.empty:
            continue
        cols_str = ' '.join(str(c).lower() for c in df.columns)
        has_date = any(h in cols_str for h in DATE_HINTS)
        has_desc = any(h in cols_str for h in DESC_HINTS)
        if has_date or has_desc:
            df.columns = df.columns.str.strip()
            return df, None

    # Fallback: just read it and hope for the best
    df = try_parse(source, 0)
    if df is not None:
        df.columns = df.columns.str.strip()
        return df, None
    return None, "Could not parse CSV file."


# ── Public API ───────────────────────────────────────────────────────────────

def parse_statement(file, password: str = '') -> tuple:
    """
    Master parser. Accepts a file-like object or path string.
    Returns (normalized_df, error_message).
    error_message is None on success.
    """
    # Detect type
    name = (file.name if hasattr(file, 'name') else str(file)).lower()
    ext = name.rsplit('.', 1)[-1] if '.' in name else ''

    if ext == 'pdf':
        raw_df, err = _read_pdf(file, password=password)
    elif ext in ('xlsx', 'xlsm'):
        raw_df, err = _read_excel(file)
    elif ext == 'xls':
        raw_df, err = _read_xls(file)
    elif ext == 'csv':
        raw_df, err = _read_csv(file)
    else:
        # Try CSV as fallback
        raw_df, err = _read_csv(file)

    if raw_df is None:
        return None, err or "Failed to read file."

    try:
        normalized = normalize_dataframe(raw_df)
    except Exception as exc:
        return None, f"Normalization error: {exc}"

    if normalized.empty:
        return None, (
            "Could not detect transaction columns. "
            "Columns found: " + ', '.join(str(c) for c in raw_df.columns)
        )

    return normalized, None


def get_detected_columns_info(file) -> dict:
    """
    Debug helper: returns which columns were detected for each role.
    Useful for showing users what was auto-detected.
    """
    name = (file.name if hasattr(file, 'name') else str(file)).lower()
    ext = name.rsplit('.', 1)[-1] if '.' in name else 'csv'

    if ext == 'pdf':
        raw_df, _ = _read_pdf(file)
    elif ext in ('xlsx', 'xlsm'):
        raw_df, _ = _read_excel(file)
    elif ext == 'xls':
        raw_df, _ = _read_xls(file)
    else:
        raw_df, _ = _read_csv(file)

    if raw_df is None:
        return {}

    cols = list(raw_df.columns)
    return {
        'all_columns': cols,
        'date':        _find_col(cols, DATE_KW),
        'description': _find_col(cols, DESC_KW),
        'debit':       _find_col(cols, DEBIT_KW),
        'credit':      _find_col(cols, CREDIT_KW),
        'amount':      _find_col(cols, AMOUNT_KW),
        'dr_cr':       _find_col(cols, DRCR_KW),
    }
