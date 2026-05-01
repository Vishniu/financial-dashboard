import pandas as pd
import sys

def analyze_statement(file_path):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return

    # In this specific CSV, Amount is column index 5, and Dr / Cr is at index 6
    # Let's dynamically find them just in case
    amount_col = 'Amount'
    dr_cr_col = df.columns[6] if len(df.columns) > 6 else 'Dr / Cr'
    
    if amount_col not in df.columns:
        print(f"Error: Could not find '{amount_col}' column.")
        return

    # Clean amount and transaction type
    df['Amount'] = df['Amount'].astype(str).str.replace(',', '').astype(float)
    df['Transaction Type'] = df[dr_cr_col].astype(str).str.strip().str.upper()

    # Define Mutual Fund mappings
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
        
        # Check Star Health (Income if CR, Premium/Expense if DR)
        if 'STAR HEALTH' in desc_upper:
            return 'Star Health Insurance'
            
        # Check LIC Insurance Brokerage
        if 'LIC INDIA D073' in desc_upper:
            return 'LIC Insurance Brokerage'
            
        # Check LIC Annuity / Income (excluding LIC Mutual fund)
        if 'LIFE INSURANCE CORPORATION' in desc_upper or ('LIC INDIA' in desc_upper and 'LIC MF' not in desc_upper):
            return 'LIC Annuity/Income'
            
        # Check Mutual Funds
        for key, value in mf_mapping.items():
            if key in desc_upper:
                return f'Mutual Fund: {value}'
                
        # --- Detailed Spending / Use-case Categorization ---
        if 'BILLPAY' in desc_upper or 'CREDITCARD' in desc_upper or 'PAID CARD NUMBER' in desc_upper:
            return 'Credit Card & Bills'
        if 'RENT' in desc_upper:
            return 'Rent'
        if 'TAX' in desc_upper or 'ETAX' in desc_upper or 'ITDTAX' in desc_upper:
            return 'Taxes'
        if 'BOND' in desc_upper or 'SHARES' in desc_upper or 'IPO' in desc_upper:
            return 'Other Investments (Bonds/Shares/IPO)'
        if 'CASH WITHDRAWAL' in desc_upper or 'ATW/' in desc_upper or 'ATL/' in desc_upper:
            return 'Cash Withdrawals'
        if 'IRCTC' in desc_upper or 'TICKET' in desc_upper:
            return 'Travel & Transport'
        if 'VODAFONE' in desc_upper or 'AIRTEL' in desc_upper or 'JIO' in desc_upper:
            return 'Telecom & Utilities'
        if 'NATIONAL PENSIO' in desc_upper or 'NPS' in desc_upper:
            return 'Pension (NPS)'
        if 'CHIT' in desc_upper:
            return 'Chit Funds'
        if 'FUEL' in desc_upper or 'PETROL' in desc_upper:
            return 'Fuel'
        if 'UPI/' in desc_upper:
            return 'UPI Transfers'
        if 'IMPS' in desc_upper:
            return 'IMPS Transfers'
        if 'NEFT' in desc_upper or 'RTGS' in desc_upper:
            return 'NEFT/RTGS Transfers'
        if 'CLG' in desc_upper or 'POST MASTER' in desc_upper:
            return 'Cheque / Postal Clearing'
            
        return 'Other Transactions'

    # Apply categorization
    df['Category'] = df['Description'].apply(get_category)

    # Group and aggregate data
    summary = df.groupby(['Category', 'Transaction Type'])['Amount'].sum().unstack(fill_value=0).reset_index()

    # Ensure both CR and DR columns exist
    if 'CR' not in summary.columns:
        summary['CR'] = 0.0
    if 'DR' not in summary.columns:
        summary['DR'] = 0.0

    # Rename columns for clarity
    summary = summary.rename(columns={'CR': 'Income (Credited CR)', 'DR': 'Expense/Investment (Deducted DR)'})

    # Add Net column for convenience
    summary['Net Value'] = summary['Income (Credited CR)'] - summary['Expense/Investment (Deducted DR)']

    # --- Calculate Grand Totals ---
    total_income = summary['Income (Credited CR)'].sum()
    
    # Investment is defined as deductions (DR) going into Mutual Funds
    mf_mask = summary['Category'].str.startswith('Mutual Fund:')
    total_investment = summary.loc[mf_mask, 'Expense/Investment (Deducted DR)'].sum()
    
    # Expense is defined as all other deductions (DR)
    total_expense = summary.loc[~mf_mask, 'Expense/Investment (Deducted DR)'].sum()

    # Format the numbers nicely for the dataframe
    for col in ['Income (Credited CR)', 'Expense/Investment (Deducted DR)', 'Net Value']:
        summary[col] = summary[col].apply(lambda x: f"Rs. {x:,.2f}")

    # Display results
    print("\n" + "="*85)
    print(" FINANCIAL STATEMENT ANALYSIS ".center(85, "="))
    print("="*85 + "\n")

    # 1. Grand Totals
    print("="*85)
    print(" GRAND TOTALS ".center(85, "="))
    print("="*85)
    print(f"Total Income (Credited)       : Rs. {total_income:,.2f}")
    print(f"Total Investment (MF Deducted): Rs. {total_investment:,.2f}")
    print(f"Total Expense (Other Deducted): Rs. {total_expense:,.2f}")
    print("="*85 + "\n")

    # 2. Total Overview
    print(summary.to_string(index=False))

    # 3. Detailed Breakdown: Mutual Funds
    print("\n" + "="*85)
    print(" MUTUAL FUNDS BREAKDOWN ".center(85, "="))
    print("="*85 + "\n")
    
    mf_df = summary[summary['Category'].str.startswith('Mutual Fund:')]
    if not mf_df.empty:
        print(mf_df.to_string(index=False))
    else:
        print("No Mutual Fund transactions found.")

    # 4. Detailed Breakdown: LIC & Star Health
    print("\n" + "="*85)
    print(" LIC & STAR HEALTH INSURANCE BREAKDOWN ".center(85, "="))
    print("="*85 + "\n")

    ins_df = summary[summary['Category'].isin(['LIC Annuity/Income', 'Star Health Insurance', 'LIC Insurance Brokerage'])]
    if not ins_df.empty:
        print(ins_df.to_string(index=False))
    else:
        print("No LIC or Star Health transactions found.")

    # 5. Detailed Breakdown: Other
    print("\n" + "="*85)
    print(" OTHER TRANSACTIONS ".center(85, "="))
    print("="*85 + "\n")
    other_df = summary[summary['Category'] == 'Other']
    if not other_df.empty:
        print(other_df.to_string(index=False))

    print("\n" + "="*85)

if __name__ == "__main__":
    # You can change the file name or pass it as an argument
    file_name = "https://docs.google.com/spreadsheets/d/1W2pJXquQ504llOg0PrCWx8ItanYcxdnXDL1Wy7Htvh0/export?format=csv&gid=1495091968"
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    
    analyze_statement(file_name)
