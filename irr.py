import streamlit as st
import pandas as pd
import plotly.graph_objs as go


def show(balance_sheet, balance_sensitivity):
    st.header("Interest Rate Risk (IRR) Simulation")

    st.subheader("Balance Sheet Preview")
    st.dataframe(balance_sheet, use_container_width=True)

    st.subheader("Scenario Definitions")
    base_shift = st.slider("Base Case Rate Shift (%)", -2.0, 2.0, 0.0, 0.25)
    shock_up = st.slider("Up Shock (%)", 0.00, 3.00, 1.00, 0.25)
    shock_down = st.slider("Down Shock (%)", 0.00, 3.00, 1.00, 0.25)

    scenarios = {
        "Base": base_shift,
        f"+{int(shock_up * 100)}bps Shock": shock_up,
        f"-{int(shock_down * 100)}bps Shock": -shock_down,
        "Stable Rates": 0.0,
        "+50bps Bear Flattener": 0.5,
        "-50bps Bull Steepener": -0.5,
    }

    base_nii = calc_nii(balance_sheet, 0.0, balance_sensitivity)
    base_eve = calc_eve(balance_sheet, 0.0)

    results = []
    for name, shift_pct in scenarios.items():
        nii = calc_nii(balance_sheet, shift_pct, balance_sensitivity)
        eve = calc_eve(balance_sheet, shift_pct)
        results.append({
            "Scenario": name,
            "Rate Shift (%)": shift_pct,
            "NII ($)": nii,
            "Δ NII ($)": nii - base_nii,
            "EVE ($)": eve,
            "Δ EVE ($)": eve - base_eve,
        })

    result_df = pd.DataFrame(results).set_index("Scenario")

    st.subheader("Scenario Results")
    st.dataframe(
        result_df.style.format({
            "Rate Shift (%)": "{:+.2f}%",
            "NII ($)": "${:,.0f}",
            "Δ NII ($)": "${:,.0f}",
            "EVE ($)": "${:,.0f}",
            "Δ EVE ($)": "${:,.0f}",
        }),
        use_container_width=True,
    )

    st.subheader("NII Sensitivity Chart")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=result_df.index, y=result_df["Δ NII ($)"], name="Change in NII"))
    fig.update_layout(yaxis_title="Δ NII ($)", xaxis_title="Scenario")
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "This module uses simplified rate-shock and duration assumptions for demonstration purposes. "
        "Production ALM models require institution-specific behavioral assumptions and validation."
    )


def calc_nii(df, rate_shift_pct, balance_sensitivity):
    scenario_df = df.copy()
    rate_shift_bps = rate_shift_pct * 100
    scenario_df["Adj Balance ($)"] = scenario_df.apply(
        lambda row: row["Amount ($)"] * (
            1 + balance_sensitivity.get(row["Product"], 0.0) * rate_shift_bps / 100
        ),
        axis=1,
    )
    scenario_df["Shifted Rate"] = scenario_df["Rate (%)"] + rate_shift_pct
    scenario_df["Annual Interest"] = scenario_df["Adj Balance ($)"] * scenario_df["Shifted Rate"] / 100

    asset_interest = scenario_df.loc[scenario_df["Type"] == "Asset", "Annual Interest"].sum()
    liability_interest = scenario_df.loc[scenario_df["Type"] == "Liability", "Annual Interest"].sum()
    return asset_interest - liability_interest


def calc_eve(df, rate_shift_pct):
    scenario_df = df.copy()
    rate_shift_decimal = rate_shift_pct / 100
    scenario_df["Shifted Value"] = scenario_df["Amount ($)"] * (
        1 - scenario_df["Duration (Years)"] * rate_shift_decimal
    )
    asset_value = scenario_df.loc[scenario_df["Type"] == "Asset", "Shifted Value"].sum()
    liability_value = scenario_df.loc[scenario_df["Type"] == "Liability", "Shifted Value"].sum()
    return asset_value - liability_value
