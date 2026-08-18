import json
import os
from datetime import datetime

import pandas as pd
import plotly.graph_objs as go
import streamlit as st

SCENARIO_FILE = "saved_scenarios.json"
KEY_TENORS = [1, 2, 5, 10, 30]
BASE_YIELD = [2.0, 2.1, 2.4, 2.8, 3.2]


def _load_saved_scenarios():
    if "saved_scenarios" not in st.session_state:
        if os.path.exists(SCENARIO_FILE):
            with open(SCENARIO_FILE, "r", encoding="utf-8") as handle:
                st.session_state.saved_scenarios = json.load(handle)
        else:
            st.session_state.saved_scenarios = []
    for scenario in st.session_state.saved_scenarios:
        scenario.setdefault("favorite", False)


def _persist_scenarios():
    with open(SCENARIO_FILE, "w", encoding="utf-8") as handle:
        json.dump(st.session_state.saved_scenarios, handle, indent=2)


def build_shocked_curve(curve_shape: str, shift_bps: int = 0, custom_shocks: list | None = None):
    if curve_shape == "Parallel Shift":
        return [y + shift_bps / 100 for y in BASE_YIELD]
    if curve_shape == "Bear Steepener":
        return [y + (i * 10) / 100 for i, y in enumerate(BASE_YIELD)]
    if curve_shape == "Bull Steepener":
        return [y - (i * 10) / 100 for i, y in enumerate(BASE_YIELD)]
    shocks = custom_shocks or [0] * len(BASE_YIELD)
    return [base + delta / 100 for base, delta in zip(BASE_YIELD, shocks)]


def scenario_builder():
    st.header("Interest Rate Scenario Builder")
    st.markdown(
        "Define and customize yield curve scenarios. "
        "Apply parallel shifts, steepeners, or tailor key rate shocks. "
        "Save and manage your scenarios below."
    )

    with st.form("scenario_form"):
        scenario_name = st.text_input("Scenario Name", value="Custom Scenario")
        curve_shape = st.selectbox(
            "Curve Shock Type",
            [
                "Parallel Shift",
                "Bear Steepener",
                "Bull Steepener",
                "Custom Key Rate Shock",
            ],
            help="Choose how the yield curve will be shocked",
        )

        shift = 0
        custom_shocks = []

        if curve_shape == "Parallel Shift":
            shift = st.slider(
                "Shift (bps)",
                -300,
                300,
                0,
                25,
                help="Apply a parallel shift to the entire curve",
            )
        elif curve_shape == "Custom Key Rate Shock":
            st.markdown("**Adjust shocks at individual key tenors (bps):**")
            for tenor in KEY_TENORS:
                custom_shocks.append(
                    st.slider(
                        f"{tenor}Y tenor shock",
                        -300,
                        300,
                        0,
                        25,
                        key=f"shock_{tenor}",
                    )
                )

        assumed_dv01 = st.number_input(
            "Assumed DV01 ($ per 1M per bp)",
            min_value=0,
            value=50,
            help="Estimate the dollar value of a one basis point move per $1M notional",
        )
        submitted = st.form_submit_button("Calculate & Preview")

    if not submitted:
        st.info("Fill the form and click 'Calculate & Preview' to see results.")
        _load_saved_scenarios()
        _render_saved_scenarios()
        return None

    shocked_yield = build_shocked_curve(curve_shape, shift, custom_shocks)

    curve_df = pd.DataFrame(
        {
            "Tenor (Years)": KEY_TENORS,
            "Base Curve (%)": BASE_YIELD,
            "Shocked Curve (%)": shocked_yield,
        }
    )

    st.subheader("Resulting Yield Curve")
    st.dataframe(
        curve_df.style.format(
            {
                "Base Curve (%)": "{:.2f}",
                "Shocked Curve (%)": "{:.2f}",
            }
        ),
        use_container_width=True,
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=KEY_TENORS, y=BASE_YIELD, name="Base Curve", mode="lines+markers")
    )
    fig.add_trace(
        go.Scatter(
            x=KEY_TENORS,
            y=shocked_yield,
            name="Shocked Curve",
            mode="lines+markers",
        )
    )
    fig.update_layout(
        title=f"Yield Curve: {scenario_name}",
        xaxis_title="Years",
        yaxis_title="Yield (%)",
        template="plotly_white",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)

    curve_bp_shift = [
        round((new - old) * 100, 1) for new, old in zip(shocked_yield, BASE_YIELD)
    ]
    impact_df = pd.DataFrame({"Tenor (Yrs)": KEY_TENORS, "Δ (bps)": curve_bp_shift})

    st.subheader("Impact Summary")
    st.table(impact_df.style.format({"Δ (bps)": "{:+}"}))

    total_dv01 = sum(bp * assumed_dv01 for bp in curve_bp_shift)
    st.metric("Total Δ MTM Estimate ($ per 1M)", f"{total_dv01:,.0f}")

    scenario_output = {
        "name": scenario_name,
        "type": curve_shape,
        "base_curve": BASE_YIELD,
        "shocked_curve": shocked_yield,
        "tenors": KEY_TENORS,
        "curve_bp_shift": curve_bp_shift,
        "dv01_estimate": total_dv01,
        "timestamp": datetime.now().isoformat(),
        "favorite": False,
    }

    _load_saved_scenarios()

    st.markdown("---")
    st.subheader("Manage Saved Scenarios")

    col1, col2 = st.columns([1, 1])
    if col1.button("Save Scenario", disabled=not scenario_name.strip()):
        names = [s["name"] for s in st.session_state.saved_scenarios]
        if scenario_name in names:
            st.warning("Scenario with this name already exists.")
        else:
            st.session_state.saved_scenarios.append(scenario_output)
            _persist_scenarios()
            st.success(f"Saved scenario '{scenario_name}'.")

    if st.session_state.saved_scenarios:
        export_df = pd.DataFrame(st.session_state.saved_scenarios)
        col2.download_button(
            label="Download CSV of Scenarios",
            data=export_df.to_csv(index=False),
            file_name="scenarios_export.csv",
            mime="text/csv",
        )
    else:
        col2.info("No saved scenarios to export.")

    _render_saved_scenarios()

    st.markdown("---")
    st.caption("Scenario builder developed for ALM & Risk Quant portfolio showcasing.")
    return scenario_output


def _render_saved_scenarios():
    if not st.session_state.get("saved_scenarios"):
        st.info("No scenarios saved yet. Use the form above to create one.")
        return

    st.subheader("Saved Scenarios List")
    df_scenarios = pd.DataFrame(st.session_state.saved_scenarios)
    df_scenarios["timestamp"] = pd.to_datetime(df_scenarios["timestamp"]).dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    df_scenarios["Favorite"] = df_scenarios["favorite"].apply(lambda x: "⭐" if x else "")
    df_display = df_scenarios[["name", "type", "dv01_estimate", "timestamp", "Favorite"]]
    df_display.columns = ["Name", "Type", "ΔMTM ($)", "Created At", "⭐"]
    df_display = df_display.sort_values(by=["⭐", "Created At"], ascending=[False, False])
    st.dataframe(df_display, use_container_width=True)

    for i, scenario in enumerate(st.session_state.saved_scenarios):
        col1, col2, _ = st.columns([1, 1, 1])
        with col1:
            if st.button(f"Delete '{scenario['name']}'", key=f"del_{i}"):
                del st.session_state.saved_scenarios[i]
                _persist_scenarios()
                st.success(f"Deleted scenario '{scenario['name']}'.")
                st.rerun()
        with col2:
            label = (
                f"Unmark Favorite '{scenario['name']}'"
                if scenario["favorite"]
                else f"Mark Favorite '{scenario['name']}'"
            )
            if st.button(label, key=f"fav_{i}"):
                st.session_state.saved_scenarios[i]["favorite"] = not scenario["favorite"]
                _persist_scenarios()
                st.rerun()
