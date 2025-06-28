import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go

def show(balance_sheet):
    st.header("Liquidity Gap Table")

    balance_sheet["Bucket"] = pd.cut(
        balance_sheet["Maturity (Months)"],
        bins=[0, 1, 3, 6, 12, 24, 36, 60, float("inf")],
        labels=["1M", "3M", "6M", "12M", "24M", "36M", "60M", ">60M"],
        right=True,
        include_lowest=True
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
