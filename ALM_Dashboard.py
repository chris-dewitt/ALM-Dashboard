import io
from pathlib import Path

import pandas as pd
import plotly.graph_objs as go
import streamlit as st

from alm_utils import summarize_balance_sheet, validate_balance_sheet
from scenario_builder import scenario_builder

SAMPLE_CSV_PATH = Path(__file__).resolve().parent / "data" / "sample_balance_sheet.csv"

BALANCE_SENSITIVITY = {
    "Fixed Mortgage": -0.01,
    "HELOC": 0.005,
    "Commercial Loan": -0.002,
    "Investment Securities": 0.0,
    "Core Checking": 0.001,
    "Savings Account": 0.002,
    "Time Deposits": 0.004,
    "FHLB Advances": 0.0,
    "Fed Funds Purchased": 0.0,
}

MODULES = [
    "Overview",
    "Liquidity Gap Table",
    "Cash Flow Gap Analysis",
    "FTP (Funds Transfer Pricing)",
    "Interest Rate Risk (IRR)",
    "Duration Gap Analysis",
    "IRR/FX Derivatives Book",
    "Scenario Builder",
]


def load_sample_csv_text() -> str:
    return SAMPLE_CSV_PATH.read_text(encoding="utf-8")


def load_balance_sheet_data(uploaded_file) -> pd.DataFrame:
    sample_text = load_sample_csv_text()

    if uploaded_file is not None:
        raw_df = pd.read_csv(uploaded_file)
        source = "Custom balance sheet loaded"
    else:
        raw_df = pd.read_csv(io.StringIO(sample_text))
        source = "Using default sample balance sheet"

    try:
        df = validate_balance_sheet(raw_df)
    except ValueError as exc:
        st.sidebar.error(f"CSV validation failed: {exc}")
        st.sidebar.info("Falling back to default sample balance sheet.")
        df = validate_balance_sheet(pd.read_csv(io.StringIO(sample_text)))
    else:
        if uploaded_file is not None:
            st.sidebar.success(source)
        else:
            st.sidebar.info(source)

    return df


def render_overview(balance_sheet: pd.DataFrame) -> None:
    st.header("Balance Sheet Overview")
    st.markdown(
        """
        Interactive Asset-Liability Management (ALM) overview of the current portfolio.
        Upload a custom balance sheet CSV in the sidebar, or explore the default sample book.
        """
    )

    kpis = summarize_balance_sheet(balance_sheet)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Assets", f"${kpis['total_assets']:,.0f}")
    col2.metric("Total Liabilities", f"${kpis['total_liabilities']:,.0f}")
    col3.metric("Equity", f"${kpis['equity']:,.0f}")
    col4.metric("Equity Ratio", f"{kpis['equity_ratio']:.1f}%")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Asset Yield", f"{kpis['asset_yield']:.2f}%")
    col6.metric("Liability Cost", f"{kpis['liability_cost']:.2f}%")
    col7.metric("Net Interest Spread", f"{kpis['net_interest_spread']:.2f}%")
    col8.metric("Simple Duration Gap", f"{kpis['simple_duration_gap']:.2f} yrs")

    pie_data = balance_sheet.groupby("Type", observed=False)["Amount ($)"].sum()
    fig_pie = go.Figure(
        data=[go.Pie(labels=pie_data.index, values=pie_data.values, hole=0.35)]
    )
    fig_pie.update_layout(title="Balance Sheet Composition by Type")
    st.plotly_chart(fig_pie, use_container_width=True)

    bar_df = balance_sheet.sort_values(by="Amount ($)", ascending=False)
    fig_bar = go.Figure()
    for balance_type in bar_df["Type"].unique():
        df_sub = bar_df[bar_df["Type"] == balance_type]
        fig_bar.add_trace(
            go.Bar(x=df_sub["Product"], y=df_sub["Amount ($)"], name=balance_type)
        )
    fig_bar.update_layout(
        title="Balance Sheet Balances by Product",
        barmode="group",
        yaxis_title="Amount ($)",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("Portfolio Detail")
    st.dataframe(
        balance_sheet.style.format(
            {
                "Amount ($)": "${:,.0f}",
                "Rate (%)": "{:.2f}",
                "Duration (Years)": "{:.2f}",
                "Maturity (Months)": "{:.0f}",
            }
        ),
        use_container_width=True,
    )


def main() -> None:
    st.set_page_config(page_title="ALM Dashboard", layout="wide")

    st.sidebar.markdown("## Upload Balance Sheet CSV")
    uploaded_file = st.sidebar.file_uploader("Upload CSV file", type="csv")
    st.sidebar.markdown("---")
    st.sidebar.markdown("## Sample Data")
    st.sidebar.download_button(
        label="Download Sample Balance Sheet CSV",
        data=load_sample_csv_text(),
        file_name="sample_balance_sheet.csv",
        mime="text/csv",
    )

    balance_sheet = load_balance_sheet_data(uploaded_file)
    selected_module = st.sidebar.selectbox("Choose Module", MODULES, index=0)

    st.title("ALM Dashboard")
    st.caption(
        "Asset-liability management analytics for liquidity, interest rate risk, FTP, and scenario analysis."
    )

    if selected_module == "Overview":
        render_overview(balance_sheet)
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

        irr.show(balance_sheet, BALANCE_SENSITIVITY)
    elif selected_module == "Duration Gap Analysis":
        import duration_gap

        duration_gap.show(balance_sheet)
    elif selected_module == "IRR/FX Derivatives Book":
        import derivatives_book

        derivatives_book.show()
    elif selected_module == "Scenario Builder":
        scenario_builder()


if __name__ == "__main__":
    main()
