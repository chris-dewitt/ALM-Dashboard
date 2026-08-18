import pandas as pd
import plotly.graph_objs as go
import streamlit as st

from alm_utils import (
    MATURITY_BINS_EXTENDED,
    MATURITY_LABELS_EXTENDED,
    assign_maturity_bucket,
    format_currency_columns,
)


def show(balance_sheet):
    st.header("Cash Flow Gap Analysis")
    st.caption(
        "Estimated monthly cash-flow run-off by maturity bucket for assets and liabilities."
    )

    cashflow_df = balance_sheet.copy()
    cashflow_df["Monthly Flow"] = cashflow_df["Amount ($)"] / cashflow_df[
        "Maturity (Months)"
    ].replace(0, 1)

    cashflow_df["Bucket"] = assign_maturity_bucket(
        cashflow_df["Maturity (Months)"],
        bins=MATURITY_BINS_EXTENDED,
        labels=MATURITY_LABELS_EXTENDED,
    )

    inflows = (
        cashflow_df.loc[cashflow_df["Type"] == "Asset"]
        .groupby("Bucket", observed=False)["Monthly Flow"]
        .sum()
    )
    outflows = (
        cashflow_df.loc[cashflow_df["Type"] == "Liability"]
        .groupby("Bucket", observed=False)["Monthly Flow"]
        .sum()
    )

    gap_cf_df = pd.DataFrame(
        {
            "Monthly Inflows ($)": inflows,
            "Monthly Outflows ($)": outflows,
        }
    ).fillna(0)
    gap_cf_df["Net Cash Flow ($)"] = (
        gap_cf_df["Monthly Inflows ($)"] - gap_cf_df["Monthly Outflows ($)"]
    )

    st.dataframe(
        format_currency_columns(
            gap_cf_df,
            ["Monthly Inflows ($)", "Monthly Outflows ($)", "Net Cash Flow ($)"],
        ),
        use_container_width=True,
    )

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=gap_cf_df.index.astype(str),
            y=gap_cf_df["Net Cash Flow ($)"],
            name="Net Cash Flow",
        )
    )
    fig.update_layout(title="Cash Flow Gap by Maturity Bucket", yaxis_title="USD")
    st.plotly_chart(fig, use_container_width=True)
