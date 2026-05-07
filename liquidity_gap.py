import streamlit as st
import pandas as pd
import plotly.graph_objs as go


def show(balance_sheet):
    st.header("Liquidity Gap Table")

    gap_source = balance_sheet.copy()
    gap_source["Bucket"] = pd.cut(
        gap_source["Maturity (Months)"],
        bins=[0, 1, 3, 6, 12, 24, 36, 60, float("inf")],
        labels=["0-1M", "1-3M", "3-6M", "6-12M", "1-2Y", "2-3Y", "3-5Y", ">5Y"],
        right=True,
        include_lowest=True,
    )

    inflows = (
        gap_source.loc[gap_source["Type"] == "Asset"]
        .groupby("Bucket", observed=False)["Amount ($)"]
        .sum()
    )
    outflows = (
        gap_source.loc[gap_source["Type"] == "Liability"]
        .groupby("Bucket", observed=False)["Amount ($)"]
        .sum()
    )

    gap_df = pd.DataFrame({"Inflows ($)": inflows, "Outflows ($)": outflows}).fillna(0)
    gap_df["Gap ($)"] = gap_df["Inflows ($)"] - gap_df["Outflows ($)"]
    gap_df["Cumulative Gap ($)"] = gap_df["Gap ($)"].cumsum()

    st.dataframe(
        gap_df.style.format({
            "Inflows ($)": "${:,.0f}",
            "Outflows ($)": "${:,.0f}",
            "Gap ($)": "${:,.0f}",
            "Cumulative Gap ($)": "${:,.0f}",
        }),
        use_container_width=True,
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(x=gap_df.index.astype(str), y=gap_df["Gap ($)"], name="Gap"))
    fig.add_trace(
        go.Scatter(
            x=gap_df.index.astype(str),
            y=gap_df["Cumulative Gap ($)"],
            mode="lines+markers",
            name="Cumulative Gap",
        )
    )
    fig.update_layout(title="Liquidity Gap by Maturity Bucket", yaxis_title="USD")
    st.plotly_chart(fig, use_container_width=True)
