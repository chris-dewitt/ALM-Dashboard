import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import io
import base64
from datetime import datetime

from scenario_builder import scenario_builder

st.set_page_config(page_title="ALM Dashboard", layout="wide")

# --- Sample balance sheet CSV ---
SAMPLE_BALANCE_SHEET_CSV = """Product,Type,Amount ($),Rate (%),Duration (Years),Maturity (Months)
Fixed Mortgage,Asset,5500000,4.0,5,60
HELOC,Asset,2700000,5.5,3,12
Commercial Loan,Asset,4200000,6.0,4,36
Investment Securities,Asset,6000000,3.0,7,84
Core Checking,Liability,3500000,0.1,1,36
Savings Account,Liability,2800000,0.3,2,24
Time Deposits,Liability,4000000,2.0,3,36
FHLB Advances,Liability,1500000,4.2,1.5,18
Fed Funds Purchased,Liability,1000000,5.0,0.5,3
"""

def get_csv_download_link(csv_string, filename="sample_balance_sheet.csv"):
    b64 = base64.b64encode(csv_string.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download Sample Balance Sheet CSV</a>'
    return href

# Sidebar upload + sample download link
st.sidebar.markdown("## Upload Balance Sheet CSV")
uploaded_file = st.sidebar.file_uploader("Upload CSV file", type="csv")
st.sidebar.markdown("---")
st.sidebar.markdown("## Sample Data")
st.sidebar.markdown(get_csv_download_link(SAMPLE_BALANCE_SHEET_CSV), unsafe_allow_html=True)

def load_balance_sheet_data():
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.sidebar.success("Custom balance sheet loaded")
    else:
        df = pd.read_csv(io.StringIO(SAMPLE_BALANCE_SHEET_CSV))
        st.sidebar.info("Using default sample balance sheet")
    return df

balance_sheet = load_balance_sheet_data()

balance_sensitivity = {
    "Fixed Mortgage": -0.01,
    "HELOC": 0.005,
    "Commercial Loan": -0.002,
    "Investment Securities": 0,
    "Core Checking": 0.001,
    "Savings Account": 0.002,
    "Time Deposits": 0.004,
    "FHLB Advances": 0,
    "Fed Funds Purchased": 0
}

modules = [
    "Overview",
    "Liquidity Gap Table",
    "Cash Flow Gap Analysis",
    "FTP (Funds Transfer Pricing)",
    "Interest Rate Risk (IRR)",
    "Duration Gap Analysis",
    "IRR/FX Derivatives Book",
    "Scenario Builder"
]

selected_module = st.sidebar.selectbox("Choose Module", modules, index=0)

st.title("ALM Dashboard")

if selected_module == "Overview":
    st.header("Balance Sheet Overview")

    st.markdown(
        """
        This dashboard provides an interactive overview of the Asset-Liability Management (ALM) balance sheet.
        
        Please use the sidebar to navigate through modules analyzing liquidity, interest rate risk, and derivative valuation impacts.
        
        You may also use the sidebar to upload your own balance sheet CSV or download the sample data.
        """
    )

    total_assets = balance_sheet[balance_sheet["Type"] == "Asset"]["Amount ($)"].sum()
    total_liabs = balance_sheet[balance_sheet["Type"] == "Liability"]["Amount ($)"].sum()
    equity = total_assets - total_liabs

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Assets", f"${total_assets:,.0f}")
    col2.metric("Total Liabilities", f"${total_liabs:,.0f}")
    col3.metric("Equity", f"${equity:,.0f}")

    pie_data = balance_sheet.groupby("Type")["Amount ($)"].sum()
    fig_pie = go.Figure(data=[go.Pie(labels=pie_data.index, values=pie_data.values, hole=0.3)])
    fig_pie.update_layout(title="Balance Sheet Composition by Type")
    st.plotly_chart(fig_pie, use_container_width=True)

    bar_df = balance_sheet.sort_values(by="Amount ($)", ascending=False)

    fig_bar = go.Figure()
    for t in bar_df["Type"].unique():
        df_sub = bar_df[bar_df["Type"] == t]
        fig_bar.add_trace(go.Bar(x=df_sub["Product"], y=df_sub["Amount ($)"], name=t))
    fig_bar.update_layout(title="Balance Sheet Balances by Product", barmode="group", yaxis_title="Amount ($)")
    st.plotly_chart(fig_bar, use_container_width=True)

elif selected_module == "Liquidity Gap Table":
    import liquidity_gap
    liquidity_gap.show(balance_sheet)

elif selected_module == "Cash Flow Gap Analysis":
    import cash_flow_gap
    cash_flow_gap.show(balance_sheet)

elif selected_module == "FTP (Funds Transfer Pricing)":
    import ftp
    ftp.show(balance_sheet)

elif selected_module == "Interest Rate Risk (IRR)":
    import irr
    irr.show(balance_sheet, balance_sensitivity)

elif selected_module == "Duration Gap Analysis":
    import duration_gap
    duration_gap.show(balance_sheet)

elif selected_module == "IRR/FX Derivatives Book":
    import derivatives_book
    derivatives_book.show()

elif selected_module == "Scenario Builder":
    scenario_builder()

