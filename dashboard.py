import streamlit as st
import pandas as pd
import altair as alt
import os

# --- Page Configuration ---
st.set_page_config(page_title="Financial Statement Dashboard", page_icon="📈", layout="wide")

# --- CSS Styling ---
st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .metric-card {
        background-color: #1e2130;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .metric-label { font-size: 18px; color: #a0aab2; }
    .metric-value { font-size: 28px; font-weight: bold; color: #4ade80; }
    .metric-value.expense { color: #f87171; }
    .metric-value.investment { color: #60a5fa; }
</style>
""", unsafe_allow_html=True)

st.title("📈 Financial Statement Dashboard")

# --- Security Layer ---
def check_password():
    """Returns `True` if the user provides the correct username and password."""
    def password_entered():
        # You can change the username and password here!
        if st.session_state["username"] == "admin" and st.session_state["password"] == "admin123":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # clear password from session state
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.info("Please login to access your secure financial data.")
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Login", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.info("Please login to access your secure financial data.")
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Login", on_click=password_entered)
        st.error("😕 Incorrect username or password")
        return False
    else:
        return True

if not check_password():
    st.stop()  # Stop rendering the rest of the app if login fails

st.markdown("Detailed breakdown of your Income, Expenses, Mutual Funds, and LIC Instruments.")

# --- Data Loading and Processing ---
@st.cache_data
def load_and_process_data(file_path):
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        st.error(f"Could not load data: {e}. If using a Google Sheet, ensure it is set to 'Anyone with the link can view'.")
        return None

    # Clean column names just in case there's whitespace
    df.columns = df.columns.str.strip()

    amount_col = 'Amount'
    dr_cr_col = df.columns[6] if len(df.columns) > 6 else 'Dr / Cr'
    
    if amount_col not in df.columns:
        return None

    df['Amount'] = df['Amount'].astype(str).str.replace(',', '').astype(float)
    df['Transaction Type'] = df[dr_cr_col].astype(str).str.strip().str.upper()
    
    # Locate Date column dynamically
    date_col = None
    for col in df.columns:
        if 'DATE' in col.upper():
            date_col = col
            break

    # Parse dates to calculate total months
    if date_col:
        df['Transaction Date'] = pd.to_datetime(df[date_col], format='mixed', dayfirst=True, errors='coerce')
        df['Month'] = df['Transaction Date'].dt.strftime('%Y-%m')
        df['Month'] = df['Month'].fillna('Unknown')
    else:
        df['Month'] = 'Unknown'

    mf_mapping = {
        'AXIS MUTUAL FUND': 'Axis Mutual Fund',
        'BARODA BNP PARIBAS': 'Baroda BNP Paribas Mutual Fund',
        'BANK OF INDIA MUTUAL FUND': 'Bank of India Mutual Fund',
        'BAJAJ MF': 'Bajaj Finserv Mutual Fund',
        'BAJAJ FINSERV': 'Bajaj Finserv Mutual Fund',
        'CANARA ROBECO': 'Canara Robeco Mutual Fund',
        'CAPITALMIND': 'Capitalmind Mutual Fund',
        'EDELWEISS': 'Edelweiss Mutual Fund',
        'GROWW': 'Groww Mutual Fund',
        'INVESCO': 'Invesco Mutual Fund',
        'ITI MUTUAL FUND': 'ITI Mutual Fund',
        'JM MUTUAL': 'JM Financial Mutual Fund',
        'JM FINANCIAL': 'JM Financial Mutual Fund',
        'LIC MF': 'LIC Mutual Fund',
        'LIC MUTUAL': 'LIC Mutual Fund',
        'MIRAE ASSET': 'Mirae Asset Mutual Fund',
        'MOTILAL OSWAL': 'Motilal Oswal Mutual Fund',
        'NIPPON INDIA': 'Nippon India Mutual Fund',
        'OLD BRIDGE': 'Old Bridge Mutual Fund',
        'NJ MUTUAL': 'NJ Mutual Fund',
        'PGIM INDIA': 'PGIM India Mutual Fund',
        'QUANTUM': 'Quantum Mutual Fund',
        'QUANT MUTUAL': 'Quant Mutual Fund',
        'SAMCO': 'Samco Mutual Fund',
        'SUNDARAM': 'Sundaram Mutual Fund',
        'TRUST MUTUAL': 'Trust Mutual Fund',
        'TAURUS': 'Taurus Mutual Fund',
        '360 ONE': '360 ONE Mutual Fund',
        'ADITYA BIRLA': 'Aditya Birla Sun Life Mutual Fund',
        'BIRLA SUNLIFE': 'Aditya Birla Sun Life Mutual Fund',
        'ANGELONE': 'AngelOne Mutual Fund',
        'BANDHAN': 'Bandhan Mutual Fund',
        'DSP MUTUAL': 'DSP Mutual Fund',
        'FRANKLIN TEMPLETON': 'Franklin Templeton Mutual Fund',
        'HDFC MUTUAL FUND': 'HDFC Mutual Fund',
        'HELIOS': 'Helios Mutual Fund',
        'HSBC MUTUAL': 'HSBC Mutual Fund',
        'ICICI PRUDENTIAL': 'ICICI Prudential Mutual Fund',
        'JIO BLACKROCK': 'Jio BlackRock Mutual Fund',
        'KOTAK MUTUAL FUND': 'Kotak Mutual Fund',
        'MAHINDRA MANULIFE': 'Mahindra Manulife Mutual Fund',
        'NAVI MUTUAL': 'Navi Mutual Fund',
        'PPFAS': 'PPFAS Mutual Fund',
        'SBI MUTUAL FUND': 'SBI Mutual Fund',
        'SBIMF': 'SBI Mutual Fund',
        'SHRIRAM MUTUAL': 'Shriram Mutual Fund',
        'TATA MUTUAL FUND': 'Tata Mutual Fund',
        'TMF BROKERAGE': 'Tata Mutual Fund',
        'UNIFI': 'Unifi Mutual Fund',
        'UNION MUTUAL': 'Union Mutual Fund',
        'WHITEOAK': 'WhiteOak Mutual Fund',
        'ZERODHA': 'Zerodha Mutual Fund',
        'UTI MF': 'UTI Mutual Fund',
        'UTI MUTUAL': 'UTI Mutual Fund',
    }

    def get_category(desc):
        desc_upper = str(desc).upper()
        if 'STAR HEALTH' in desc_upper:
            return 'Star Health Insurance'
        if 'LIC INDIA D073' in desc_upper:
            return 'LIC Insurance Brokerage'
        if 'LIFE INSURANCE CORPORATION' in desc_upper or ('LIC INDIA' in desc_upper and 'LIC MF' not in desc_upper):
            return 'LIC Annuity/Income'
        for key, value in mf_mapping.items():
            if key in desc_upper:
                return f'MF: {value}'
                
        # --- Detailed Spending / Use-case Categorization ---
        if 'BILLPAY' in desc_upper or 'CREDITCARD' in desc_upper or 'PAID CARD NUMBER' in desc_upper:
            return '💳 Credit Card & Bills'
        if 'RENT' in desc_upper:
            return '🏠 Rent'
        if 'TAX' in desc_upper or 'ETAX' in desc_upper or 'ITDTAX' in desc_upper:
            return '🏛️ Taxes'
        if 'BOND' in desc_upper or 'SHARES' in desc_upper or 'IPO' in desc_upper:
            return '📈 Other Investments (Bonds/Shares/IPO)'
        if 'CASH WITHDRAWAL' in desc_upper or 'ATW/' in desc_upper or 'ATL/' in desc_upper:
            return '🏧 Cash Withdrawals'
        if 'IRCTC' in desc_upper or 'TICKET' in desc_upper:
            return '🚆 Travel & Transport'
        if 'VODAFONE' in desc_upper or 'AIRTEL' in desc_upper or 'JIO' in desc_upper:
            return '📱 Telecom & Utilities'
        if 'NATIONAL PENSIO' in desc_upper or 'NPS' in desc_upper:
            return '👴 Pension (NPS)'
        if 'CHIT' in desc_upper:
            return '💰 Chit Funds'
        if 'FUEL' in desc_upper or 'PETROL' in desc_upper:
            return '⛽ Fuel'
        if 'UPI/' in desc_upper:
            return '💸 UPI Transfers'
        if 'IMPS' in desc_upper:
            return '🏦 IMPS Transfers'
        if 'NEFT' in desc_upper or 'RTGS' in desc_upper:
            return '🏦 NEFT/RTGS Transfers'
        if 'CLG' in desc_upper or 'POST MASTER' in desc_upper:
            return '📝 Cheque / Postal Clearing'
            
        return 'Other Transactions'

    df['Category'] = df['Description'].apply(get_category)
    return df

# --- Plug & Play Data Source ---
st.sidebar.header("📁 Data Source")
st.sidebar.markdown("Plug and play your financial statement:")
data_source_link = st.sidebar.text_input("Google Sheets CSV Export Link", placeholder="https://docs.google.com/...")
uploaded_file = st.sidebar.file_uploader("Or upload a local CSV file", type=["csv"])

# Load Data
df = None
if uploaded_file is not None:
    df = load_and_process_data(uploaded_file)
elif data_source_link:
    df = load_and_process_data(data_source_link)

if df is None:
    st.info("👈 Please drop your Google Sheets CSV link or upload a CSV file in the sidebar to securely generate your dashboard!")
    st.stop()

# Calculate date span
if 'Transaction Date' in df.columns and pd.api.types.is_datetime64_any_dtype(df['Transaction Date']):
    min_date = df['Transaction Date'].min()
    max_date = df['Transaction Date'].max()
    total_months = (max_date.year - min_date.year) * 12 + max_date.month - min_date.month + 1
    total_months = max(1, total_months) # Prevent division by zero
else:
    total_months = 1

# Aggregate Data
summary = df.groupby(['Category', 'Transaction Type'])['Amount'].sum().unstack(fill_value=0).reset_index()
for col in ['CR', 'DR']:
    if col not in summary.columns:
        summary[col] = 0.0

summary = summary.rename(columns={'CR': 'Income (CR)', 'DR': 'Expense/Investment (DR)'})
summary['Net Value'] = summary['Income (CR)'] - summary['Expense/Investment (DR)']
summary['Avg Monthly Income'] = summary['Income (CR)'] / total_months

mf_mask = summary['Category'].str.startswith('MF:')
total_income = summary['Income (CR)'].sum()
avg_monthly_mf_income = summary.loc[mf_mask, 'Income (CR)'].sum() / total_months
total_expense = summary.loc[~mf_mask, 'Expense/Investment (DR)'].sum()

# --- Grand Totals ---
st.markdown("### 📊 Grand Totals Overview")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Total Income (Credited)</div>
        <div class='metric-value'>₹ {total_income:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Avg MF Income / Month</div>
        <div class='metric-value investment'>₹ {avg_monthly_mf_income:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Total Expense (Other Deducted)</div>
        <div class='metric-value expense'>₹ {total_expense:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- Visualizations ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏛️ Mutual Fund Breakdown", "🛡️ LIC & Star Health", "💸 Spending Breakdown", "📅 MoM Trend", "📈 Full Statement View"])

with tab1:
    st.subheader("Mutual Fund House Breakdown")
    mf_df = summary[mf_mask].copy()
    mf_df['Category'] = mf_df['Category'].str.replace('MF: ', '')
    
    if mf_df.empty:
        st.info("No Mutual Fund transactions found.")
    else:
        # Chart
        c1, c2 = st.columns([2, 1])
        with c1:
            chart_data = mf_df.melt(id_vars=['Category'], value_vars=['Income (CR)', 'Avg Monthly Income'], var_name='Type', value_name='Amount')
            chart_data = chart_data[chart_data['Amount'] > 0] # Filter 0 values
            
            bar_chart = alt.Chart(chart_data).mark_bar().encode(
                x=alt.X('Amount:Q', title='Amount (₹)'),
                y=alt.Y('Category:N', sort='-x', title='Fund House'),
                color=alt.Color('Type:N', scale=alt.Scale(domain=['Income (CR)', 'Avg Monthly Income'], range=['#4ade80', '#60a5fa'])),
                tooltip=['Category', 'Type', alt.Tooltip('Amount:Q', format=',.2f')]
            ).properties(height=500).interactive()
            st.altair_chart(bar_chart, width='stretch')
            
        with c2:
            st.dataframe(mf_df[['Category', 'Income (CR)', 'Avg Monthly Income']].style.format({"Income (CR)": "₹ {:,.2f}", "Avg Monthly Income": "₹ {:,.2f}"}), hide_index=True)

with tab2:
    st.subheader("Insurance & Annuity Instruments")
    ins_df = summary[summary['Category'].isin(['LIC Annuity/Income', 'Star Health Insurance', 'LIC Insurance Brokerage'])].copy()
    
    if ins_df.empty:
        st.info("No LIC or Star Health transactions found.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            # Prepare data for pie chart
            ins_chart_data = ins_df[['Category', 'Income (CR)']]
            ins_chart_data = ins_chart_data[ins_chart_data['Income (CR)'] > 0]
            
            if not ins_chart_data.empty:
                pie_chart = alt.Chart(ins_chart_data).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta(field="Income (CR)", type="quantitative"),
                    color=alt.Color(field="Category", type="nominal", scale=alt.Scale(scheme='set2')),
                    tooltip=['Category', alt.Tooltip('Income (CR):Q', format=',.2f')]
                ).properties(title="Income Distribution from Insurance")
                st.altair_chart(pie_chart, width='stretch')
            else:
                st.write("No Income recorded from LIC or Star Health.")
                
        with c2:
            st.dataframe(ins_df.style.format({"Income (CR)": "₹ {:,.2f}", "Expense/Investment (DR)": "₹ {:,.2f}", "Net Value": "₹ {:,.2f}"}), hide_index=True)

with tab3:
    st.subheader("Spending Analysis (Detailed Breakdown)")
    
    # Filter for all Expense categories excluding Mutual funds
    spending_df = summary[(~summary['Category'].str.startswith('MF:')) & 
                          (~summary['Category'].isin(['LIC Annuity/Income', 'Star Health Insurance', 'LIC Insurance Brokerage'])) & 
                          (summary['Expense/Investment (DR)'] > 0)].copy()
    
    if spending_df.empty:
        st.info("No spending transactions found.")
    else:
        # Sort by largest expense
        spending_df = spending_df.sort_values(by='Expense/Investment (DR)', ascending=False)
        
        c1, c2 = st.columns([1, 1])
        with c1:
            pie_chart_expense = alt.Chart(spending_df).mark_arc(innerRadius=40).encode(
                theta=alt.Theta(field="Expense/Investment (DR)", type="quantitative"),
                color=alt.Color(field="Category", type="nominal", scale=alt.Scale(scheme='tableau20')),
                tooltip=['Category', alt.Tooltip('Expense/Investment (DR):Q', format=',.2f')]
            ).properties(title="Where is your money going?", height=400)
            st.altair_chart(pie_chart_expense, width='stretch')
            
        with c2:
            bar_chart_expense = alt.Chart(spending_df).mark_bar().encode(
                x=alt.X('Expense/Investment (DR):Q', title='Amount (₹)'),
                y=alt.Y('Category:N', sort='-x', title='Expense Category'),
                color=alt.Color('Category:N', legend=None),
                tooltip=['Category', alt.Tooltip('Expense/Investment (DR):Q', format=',.2f')]
            ).properties(title="Spending by Category", height=400)
            st.altair_chart(bar_chart_expense, width='stretch')
            
        st.dataframe(spending_df[['Category', 'Expense/Investment (DR)']].style.format({"Expense/Investment (DR)": "₹ {:,.2f}"}), width='stretch', hide_index=True)

with tab4:
    st.subheader("Month-on-Month Income vs Expense")
    
    if 'Month' in df.columns and df['Month'].nunique() > 0 and not df[df['Month'] != 'Unknown'].empty:
        # Filter out unknown months
        mom_valid = df[df['Month'] != 'Unknown']
        
        # Aggregate by Month and Transaction Type
        mom_df = mom_valid.groupby(['Month', 'Transaction Type'])['Amount'].sum().unstack(fill_value=0).reset_index()
        
        if 'CR' not in mom_df.columns: mom_df['CR'] = 0.0
        if 'DR' not in mom_df.columns: mom_df['DR'] = 0.0
        
        mom_df = mom_df.rename(columns={'CR': 'Income (CR)', 'DR': 'Expense/Investment (DR)'})
        mom_df['Net Savings'] = mom_df['Income (CR)'] - mom_df['Expense/Investment (DR)']
        mom_df = mom_df.sort_values(by='Month')
        
        c1, c2 = st.columns([2, 1])
        with c1:
            # Melt for chart
            chart_data = mom_df.melt(id_vars=['Month'], value_vars=['Income (CR)', 'Expense/Investment (DR)'], var_name='Type', value_name='Amount')
            
            bar_chart_mom = alt.Chart(chart_data).mark_bar().encode(
                x=alt.X('Month:N', title='Month'),
                y=alt.Y('Amount:Q', title='Amount (₹)'),
                color=alt.Color('Type:N', scale=alt.Scale(domain=['Income (CR)', 'Expense/Investment (DR)'], range=['#4ade80', '#f87171'])),
                xOffset=alt.XOffset('Type:N'),
                tooltip=['Month', 'Type', alt.Tooltip('Amount:Q', format=',.2f')]
            ).properties(height=400, title="Monthly Cashflow").interactive()
            
            st.altair_chart(bar_chart_mom, width='stretch')
            
        with c2:
            st.dataframe(mom_df.style.format({"Income (CR)": "₹ {:,.2f}", "Expense/Investment (DR)": "₹ {:,.2f}", "Net Savings": "₹ {:,.2f}"}), hide_index=True)
            
    else:
        st.info("Not enough date information found to calculate Month-on-Month trends.")

with tab5:
    st.subheader("Complete Aggregated Statement")
    
    # Sort to show largest incomes and expenses
    sorted_summary = summary.sort_values(by=['Income (CR)', 'Expense/Investment (DR)'], ascending=[False, False])
    st.dataframe(sorted_summary.style.format({"Income (CR)": "₹ {:,.2f}", "Expense/Investment (DR)": "₹ {:,.2f}", "Net Value": "₹ {:,.2f}"}), width='stretch', hide_index=True)
    
    with st.expander("Show Raw Transaction Log"):
        st.dataframe(df.style.format({'Amount': "₹ {:,.2f}"}), hide_index=True)
