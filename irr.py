import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go

def show(balance_sheet, balance_sensitivity):
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
            return None
        df["Shifted Value"] = df["Amount ($)"] * (1 - df["Duration (Years)"] * rate_shift_decimal)
        df["Impact"] = df["Shifted Value"] - df["Amount ($)"]
        eve = df[df["Type"] == "Asset"]["Shifted Value"].sum() - df[df["Type"] == "Liability"]["Shifted Value"].sum()
        return eve

    results = []
    for name, shift in scenarios.items():
        nii = calc_nii(balance_sheet, shift)
        eve = calc_eve(balance_sheet, shift * 100)
        results.append({"Scenario": name, "NII ($)": nii, "EVE ($)": eve})

    result_df = pd.DataFrame(results).set_index("Scenario")
    st.subheader("Scenario Results")
    st.dataframe(result_df.style.format({"NII ($)": "${:,.0f}", "EVE ($)": "${:,.0f}"}), use_container_width=True)

    st.subheader("NII Sensitivity Chart")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=result_df.index, y=result_df["NII ($)"], name="Net Interest Income"))
    fig.update_layout(yaxis_title="NII ($)", xaxis_title="Scenario")
    st.plotly_chart(fig, use_container_width=True)
