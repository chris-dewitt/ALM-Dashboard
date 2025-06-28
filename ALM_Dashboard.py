import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import io
import base64
from datetime import datetime

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
    "IRR/FX Derivatives Book"
]

# Sidebar dropdown navigation for all pages
selected_module = st.sidebar.selectbox("Choose Module", modules, index=0)

st.title("ALM Dashboard")

# Landing page - just the overview, no navigation buttons
if selected_module == "Overview":
    st.header("Balance Sheet Overview")

    st.markdown(
        """
        This dashboard provides an interactive overview of the Asset-Liability Management (ALM) balance sheet.
        \n\nPlease use the sidebar to navigate through modules analyzing liquidity, interest rate risk, and derivative valuation impacts.
        \nYou may also use the sidebar to upload your own balance sheet CSV or download the sample data.
        \n\n\n
    
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

    bar_df = balance_sheet.copy()
    bar_df = bar_df.sort_values(by="Amount ($)", ascending=False)

    fig_bar = go.Figure()
    for t in bar_df["Type"].unique():
        df_sub = bar_df[bar_df["Type"] == t]
        fig_bar.add_trace(go.Bar(x=df_sub["Product"], y=df_sub["Amount ($)"], name=t))
    fig_bar.update_layout(title="Balance Sheet Balances by Product", barmode="group", yaxis_title="Amount ($)")
    st.plotly_chart(fig_bar, use_container_width=True)

else:
    # Back to Overview button in modules
    if st.button("Back to Overview"):
        st.experimental_set_query_params(module="Overview")
        st.experimental_rerun()

    if selected_module == "Liquidity Gap Table":
        st.header("Liquidity Gap Table")

        balance_sheet["Bucket"] = pd.cut(
            balance_sheet["Maturity (Months)"],
            bins=[0, 1, 3, 6, 12, 24, 36, 60, np.inf],
            labels=["1M", "3M", "6M", "12M", "24M", "36M", "60M", ">60M"],
            right=True
        )
        inflows = balance_sheet[balance_sheet["Type"] == "Asset"].groupby("Bucket")["Amount ($)"].sum()
        outflows = balance_sheet[balance_sheet["Type"] == "Liability"].groupby("Bucket")["Amount ($)"].sum()
        gap_df = pd.DataFrame({
            "Inflows ($)": inflows,
            "Outflows ($)": outflows
        }).fillna(0)
        gap_df["Gap ($)"] = gap_df["Inflows ($)"] - gap_df["Outflows ($)"]
        gap_df["Cumulative Gap ($)"] = gap_df["Gap ($)"].cumsum()
        st.dataframe(gap_df, use_container_width=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(x=gap_df.index, y=gap_df["Gap ($)"], name="Gap"))
        fig.add_trace(go.Scatter(x=gap_df.index, y=gap_df["Cumulative Gap ($)"],
                                mode="lines+markers", name="Cumulative Gap"))
        fig.update_layout(title="Liquidity Gap by Maturity Bucket", yaxis_title="USD")
        st.plotly_chart(fig, use_container_width=True)

    elif selected_module == "Cash Flow Gap Analysis":
        st.header("Cash Flow Gap Analysis")

        cashflow_df = balance_sheet.copy()
        cashflow_df["Monthly Flow"] = cashflow_df["Amount ($)"] / cashflow_df["Maturity (Months)"].replace(0, 1)
        buckets = [1, 3, 6, 12, 24, 36, 60, 120]
        bucket_labels = ["1M", "3M", "6M", "12M", "24M", "36M", "60M", ">60M"]
        cashflow_df["Bucket"] = pd.cut(
            cashflow_df["Maturity (Months)"],
            bins=[0] + buckets + [np.inf],
            labels=bucket_labels,
            right=True
        )
        inflows = cashflow_df[cashflow_df["Type"] == "Asset"].groupby("Bucket")["Monthly Flow"].sum()
        outflows = cashflow_df[cashflow_df["Type"] == "Liability"].groupby("Bucket")["Monthly Flow"].sum()
        gap_cf_df = pd.DataFrame({
            "Monthly Inflows ($)": inflows,
            "Monthly Outflows ($)": outflows
        }).fillna(0)
        gap_cf_df["Net Cash Flow ($)"] = gap_cf_df["Monthly Inflows ($)"] - gap_cf_df["Monthly Outflows ($)"]
        st.dataframe(gap_cf_df, use_container_width=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(x=gap_cf_df.index, y=gap_cf_df["Net Cash Flow ($)"], name="Net Cash Flow"))
        fig.update_layout(title="Cash Flow Gap by Maturity Bucket", yaxis_title="USD")
        st.plotly_chart(fig, use_container_width=True)

    elif selected_module == "FTP (Funds Transfer Pricing)":
        st.header("Funds Transfer Pricing")

        ftp_df = balance_sheet.copy()
        ftp_curve = {
            12: 1.0,
            24: 1.5,
            36: 2.0,
            60: 2.5,
            84: 3.0,
            120: 3.5
        }

        def map_ftp_rate(months):
            for m in sorted(ftp_curve):
                if months <= m:
                    return ftp_curve[m]
            return max(ftp_curve.values())

        ftp_df["FTP Rate"] = ftp_df["Maturity (Months)"].apply(map_ftp_rate)
        ftp_df["FTP Charge ($)"] = ftp_df["Amount ($)"] * ftp_df["FTP Rate"] / 100
        ftp_df["FTP Net ($)"] = ftp_df["Amount ($)"] * (ftp_df["Rate (%)"] - ftp_df["FTP Rate"]) / 100

        st.dataframe(ftp_df[["Product", "Type", "Amount ($)", "Rate (%)", "FTP Rate", "FTP Net ($)"]], use_container_width=True)

        ftp_summary = ftp_df.groupby("Type")["FTP Net ($)"].sum()
        st.subheader("FTP Contribution by Type")
        st.bar_chart(ftp_summary)

    elif selected_module == "Interest Rate Risk (IRR)":
        st.header("Interest Rate Risk (IRR) Simulation")

        st.subheader("Balance Sheet Preview")
        st.dataframe(balance_sheet, use_container_width=True)

        st.subheader("Scenario Definitions")
        base_shift = st.slider("Base Case Rate Shift (%)", -2.0, 2.0, 0.0, 0.25)
        shock_up = st.slider("+100 bps Shock", 0.00, 3.00, 1.00, 0.25)
        shock_down = st.slider("-100 bps Shock", 0.00, 3.00, 1.00, 0.25)

        scenarios = {
            "Base": base_shift,
            "+100bps Shock": shock_up,
            "-100bps Shock": -shock_down,
            "Stable Rates": 0.0,
            "+50bps Bear Flattener": 0.5,
            "-50bps Bull Steepener": -0.5
        }

        def calc_nii(df, rate_shift):
            df = df.copy()
            rate_shift_bps = rate_shift * 100
            df["Adj Balance ($)"] = df.apply(
                lambda row: row["Amount ($)"] * (1 + balance_sensitivity.get(row["Product"], 0) * rate_shift_bps / 100),
                axis=1
            )
            df["Shifted Rate"] = df["Rate (%)"] + rate_shift
            df["Annual Interest"] = df["Adj Balance ($)"] * df["Shifted Rate"] / 100
            nii = df[df["Type"] == "Asset"]["Annual Interest"].sum() - df[df["Type"] == "Liability"]["Annual Interest"].sum()
            return nii

        def calc_eve(df, rate_shift):
            df = df.copy()
            rate_shift_decimal = rate_shift / 100
            if "Duration (Years)" not in df.columns:
                df["Duration (Years)"] = 3.0
            df["Adj Balance ($)"] = df["Amount ($)"]
            df["ΔEVE"] = -df["Adj Balance ($)"] * df["Duration (Years)"] * rate_shift_decimal
            eve = df[df["Type"] == "Asset"]["ΔEVE"].sum() + df[df["Type"] == "Liability"]["ΔEVE"].sum()
            return eve

        st.subheader("NII and EVE Scenario Table")
        results = []
        for label, shift in scenarios.items():
            nii = calc_nii(balance_sheet, shift)
            eve = calc_eve(balance_sheet, shift)
            results.append({"Scenario": label, "Rate Shift (%)": shift, "NII ($)": nii, "ΔEVE ($)": eve})

        results_df = pd.DataFrame(results)
        base_nii = results_df.loc[results_df["Scenario"] == "Base", "NII ($)"].values[0]
        results_df["Δ from Base NII ($)"] = results_df["NII ($)"] - base_nii

        st.dataframe(results_df, use_container_width=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(x=results_df["Scenario"], y=results_df["NII ($)"], name="NII"))
        fig.add_trace(go.Scatter(x=results_df["Scenario"], y=results_df["ΔEVE ($)"],
                                 mode="lines+markers", name="ΔEVE", yaxis="y2"))

        fig.update_layout(
            title="Net Interest Income and Economic Value Change by Scenario",
            yaxis=dict(title="NII ($)"),
            yaxis2=dict(title="ΔEVE ($)", overlaying="y", side="right"),
            legend=dict(x=0.5, y=1.1, orientation="h")
        )
        st.plotly_chart(fig, use_container_width=True)

    elif selected_module == "Duration Gap Analysis":
        st.header("Duration Gap Analysis")

        duration_df = balance_sheet.copy()
        if "Duration (Years)" not in duration_df.columns:
            duration_df["Duration (Years)"] = 3.0

        duration_df["Weighted Duration"] = duration_df["Duration (Years)"] * duration_df["Amount ($)"]
        total_assets = duration_df[duration_df["Type"] == "Asset"]["Amount ($)"].sum()
        total_liabilities = duration_df[duration_df["Type"] == "Liability"]["Amount ($)"].sum()
        dur_assets = duration_df[duration_df["Type"] == "Asset"]["Weighted Duration"].sum() / total_assets
        dur_liabs = duration_df[duration_df["Type"] == "Liability"]["Weighted Duration"].sum() / total_liabilities
        dur_gap = dur_assets - dur_liabs

        st.metric("Asset Duration (Years)", f"{dur_assets:.2f}")
        st.metric("Liability Duration (Years)", f"{dur_liabs:.2f}")
        st.metric("Duration Gap (Years)", f"{dur_gap:.2f}")

    elif selected_module == "IRR/FX Derivatives Book":
        st.header("IRR & FX Derivatives Portfolio")

        st.sidebar.markdown("### Upload Derivatives CSV")
        uploaded_deriv_file = st.sidebar.file_uploader(
            "Upload Derivatives File",
            type="csv",
            help="Expected columns: Instrument, Notional ($), Type (IRR/FX), Strike Rate (%), Maturity (Months), Current MTM ($)"
        )

        if uploaded_deriv_file:
            derivatives_data = pd.read_csv(uploaded_deriv_file)
            expected_columns = ["Instrument", "Notional ($)", "Type", "Strike Rate (%)", "Maturity (Months)", "Current MTM ($)"]
            missing_cols = [col for col in expected_columns if col not in derivatives_data.columns]
            if missing_cols:
                st.error(f"Missing columns in uploaded file: {', '.join(missing_cols)}")
                st.stop()
            else:
                st.sidebar.success("Custom derivative book loaded")
        else:
            derivatives_data = pd.DataFrame({
                "Instrument": ["USD Swaption", "USD IRS Pay-Fixed", "EUR/USD FX Swap", "USD Cap", "USD Floor"],
                "Notional ($)": [5000000, 10000000, 3000000, 2000000, 1500000],
                "Type": ["IRR", "IRR", "FX", "IRR", "IRR"],
                "Strike Rate (%)": [3.0, 2.5, np.nan, 4.0, 1.0],
                "Maturity (Months)": [12, 60, 3, 24, 24],
                "Current MTM ($)": [200000, -150000, 50000, 75000, -25000]
            })
            st.sidebar.info("Using sample derivative portfolio")

            sample_template = derivatives_data.to_csv(index=False)
            b64_template = base64.b64encode(sample_template.encode()).decode()
            template_link = f'<a href="data:file/csv;base64,{b64_template}" download="sample_derivatives_template.csv">Download Sample Derivatives Template</a>'
            st.sidebar.markdown(template_link, unsafe_allow_html=True)

        st.dataframe(derivatives_data, use_container_width=True)

        st.subheader("Scenario Shocks")

        st.markdown("#### FX Spot Rate Settings")
        base_fx_rate = st.number_input("Base Spot Rate (e.g. EUR/USD)", min_value=0.5, max_value=2.0, value=1.10, step=0.01)
        fx_shock = st.slider("FX Spot Shock (Δ%)", -10.0, 10.0, 0.0, 0.5)
        fx_shock_pct = fx_shock / 100
        new_fx_rate = base_fx_rate * (1 + fx_shock_pct)
        st.markdown(f"**New FX Rate After Shock:** {new_fx_rate:.4f}")

        irr_shock = st.slider("IR Curve Parallel Shift (%)", -2.0, 2.0, 0.0, 0.25)

        shock_results = derivatives_data.copy()
        shock_results["ΔMTM IRR"] = np.where(
            shock_results["Type"] == "IRR",
            shock_results["Notional ($)"] * (irr_shock / 100) * shock_results["Maturity (Months)"] / 12 * 0.01,
            0.0
        )
        shock_results["ΔMTM FX"] = np.where(
            shock_results["Type"] == "FX",
            shock_results["Notional ($)"] * fx_shock_pct,
            0.0
        )
        shock_results["Total ΔMTM ($)"] = shock_results["ΔMTM IRR"] + shock_results["ΔMTM FX"]
        shock_results["New MTM ($)"] = shock_results["Current MTM ($)"] + shock_results["Total ΔMTM ($)"]

        st.subheader("Valuation Changes")
        st.dataframe(shock_results[["Instrument", "Notional ($)", "Type", "Current MTM ($)", "Total ΔMTM ($)", "New MTM ($)"]], use_container_width=True)

        mtm_total = shock_results[["Current MTM ($)", "New MTM ($)"]].sum().rename("Portfolio")
        st.metric("Change in Portfolio MTM", f"${mtm_total['New MTM ($)'] - mtm_total['Current MTM ($)']:,.0f}")

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=shock_results["Instrument"], y=shock_results["New MTM ($)"], name="New MTM"))
        fig2.add_trace(go.Bar(x=shock_results["Instrument"], y=shock_results["Current MTM ($)"], name="Current MTM"))
        fig2.update_layout(barmode="group", title="Derivative MTM by Instrument")
        st.plotly_chart(fig2, use_container_width=True)

        export_csv = shock_results.to_csv(index=False)
        b64_csv = base64.b64encode(export_csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64_csv}" download="derivative_mtm_{datetime.now().strftime("%Y%m%d")}.csv">Download Derivatives Report</a>'
        st.markdown(href, unsafe_allow_html=True)
