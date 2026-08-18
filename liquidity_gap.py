import pandas as pd
import plotly.graph_objs as go
import streamlit as st

from alm_utils import assign_maturity_bucket, format_currency_columns


def show(balance_sheet):
    st.header("Liquidity Gap Table")
    st.caption(
        "Maturity-bucketed asset inflows versus liability outflows, with cumulative funding gap."
    )

    gap_source = balance_sheet.copy()
    gap_source["Bucket"] = assign_maturity_bucket(gap_source["Maturity (Months)"])

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
        format_currency_columns(
            gap_df,
            ["Inflows ($)", "Outflows ($)", "Gap ($)", "Cumulative Gap ($)"],
        ),
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

    min_cum = float(gap_df["Cumulative Gap ($)"].min())
    if min_cum < 0:
        st.warning(
            f"Cumulative funding gap reaches ${min_cum:,.0f}. "
            "Negative cumulative gaps indicate potential refinancing or liquidity pressure."
        )
    else:
        st.success("Cumulative liquidity gap remains non-negative across all buckets.")
