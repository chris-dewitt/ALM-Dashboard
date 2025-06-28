import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go

def show(balance_sheet):
    st.header("Cash Flow Gap Analysis")

    cashflow_df = balance_sheet.copy()
    cashflow_df["Monthly Flow"] = cashflow_df["Amount ($)"] / cashflow_df["Maturity (Months)"].replace(0, 1)

    buckets = [0, 1, 3, 6, 12, 24, 36, 60, 120]
    bucket_labels = ["<1M", "1–3M", "3–6M", "6–12M", "1–2Y", "2–5Y", "5–10Y", ">10Y"]

    cashflow_df["Bucket"] = pd.cut(
        cashflow_df["Maturity (Months)"],
        bins=buckets,
        labels=bucket_labels,
        right=True,
        include_lowest=True
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
