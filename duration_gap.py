import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go

def show(balance_sheet):
    st.header("Duration Gap Analysis")

    if "Duration (Years)" not in balance_sheet.columns:
        st.error("Duration column missing from balance sheet data.")
        return

    duration_assets = balance_sheet[balance_sheet["Type"] == "Asset"].copy()
    duration_liabs = balance_sheet[balance_sheet["Type"] == "Liability"].copy()

    da = (duration_assets["Amount ($)"] * duration_assets["Duration (Years)"]).sum()
    la = duration_liabs["Amount ($)"].sum()
    dl = (duration_liabs["Amount ($)"] * duration_liabs["Duration (Years)"]).sum()
    da_total = duration_assets["Amount ($)"].sum()

    if la == 0 or da_total == 0:
        st.error("Liabilities or Assets sum to zero, cannot calculate duration gap.")
        return

    weighted_avg_asset_duration = da / da_total
    weighted_avg_liab_duration = dl / la
    duration_gap = weighted_avg_asset_duration - weighted_avg_liab_duration

    st.metric("Weighted Avg Asset Duration (Years)", f"{weighted_avg_asset_duration:.2f}")
    st.metric("Weighted Avg Liability Duration (Years)", f"{weighted_avg_liab_duration:.2f}")
    st.metric("Duration Gap (Years)", f"{duration_gap:.2f}")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Assets", "Liabilities"],
        y=[weighted_avg_asset_duration, weighted_avg_liab_duration],
        name="Duration"
    ))
    fig.update_layout(title="Weighted Average Duration Comparison", yaxis_title="Duration (Years)")
    st.plotly_chart(fig, use_container_width=True)
