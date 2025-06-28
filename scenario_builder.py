import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import json
import os
import base64
from datetime import datetime

def scenario_builder():
    st.header("Interest Rate Scenario Builder")
    st.markdown(
        "Define and customize yield curve scenarios. "
        "Apply parallel shifts, steepeners, or tailor key rate shocks. "
        "Save and manage your scenarios below."
    )

    # Layout containers for form
    with st.form("scenario_form"):
        scenario_name = st.text_input("Scenario Name", value="Custom Scenario")
        curve_shape = st.selectbox("Curve Shock Type", [
            "Parallel Shift",
            "Bear Steepener",
            "Bull Steepener",
            "Custom Key Rate Shock"
        ], help="Choose how the yield curve will be shocked")

        key_tenors = [1, 2, 5, 10, 30]  # years
        base_yield = [2.0, 2.1, 2.4, 2.8, 3.2]

        shocked_yield = []

        if curve_shape == "Parallel Shift":
            shift = st.slider("Shift (bps)", -300, 300, 0, 25,
                              help="Apply a parallel shift to the entire curve")
            shocked_yield = [y + shift / 100 for y in base_yield]

        elif curve_shape == "Bear Steepener":
            shocked_yield = [y + (i * 10) / 100 for i, y in enumerate(base_yield)]

        elif curve_shape == "Bull Steepener":
            shocked_yield = [y - (i * 10) / 100 for i, y in enumerate(base_yield)]

        elif curve_shape == "Custom Key Rate Shock":
            st.markdown("**Adjust shocks at individual key tenors (bps):**")
            for tenor, base in zip(key_tenors, base_yield):
                delta = st.slider(f"{tenor}Y tenor shock", -300, 300, 0, 25, key=f"shock_{tenor}")
                shocked_yield.append(base + delta / 100)

        assumed_dv01 = st.number_input("Assumed DV01 ($ per 1M per bp)", min_value=0, value=50,
                                       help="Estimate the dollar value of a one basis point move per $1M notional")

        submitted = st.form_submit_button("Calculate & Preview")

    if not submitted:
        st.info("Fill the form and click 'Calculate & Preview' to see results.")
        return

    # Display results once submitted
    curve_df = pd.DataFrame({
        "Tenor (Years)": key_tenors,
        "Base Curve (%)": base_yield,
        "Shocked Curve (%)": shocked_yield
    })

    st.subheader("Resulting Yield Curve")
    st.dataframe(curve_df, use_container_width=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=key_tenors, y=base_yield, name="Base Curve", mode="lines+markers"))
    fig.add_trace(go.Scatter(x=key_tenors, y=shocked_yield, name="Shocked Curve", mode="lines+markers"))
    fig.update_layout(
        title=f"Yield Curve: {scenario_name}",
        xaxis_title="Years",
        yaxis_title="Yield (%)",
        template="plotly_white",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)

    curve_bp_shift = [round((new - old) * 100, 1) for new, old in zip(shocked_yield, base_yield)]
    impact_df = pd.DataFrame({"Tenor (Yrs)": key_tenors, "Δ (bps)": curve_bp_shift})

    st.subheader("Impact Summary")
    st.table(impact_df.style.format({"Δ (bps)": "{:+}"}))

    total_dv01 = sum([bp * assumed_dv01 for bp in curve_bp_shift])
    st.metric("Total Δ MTM Estimate ($ per 1M)", f"{total_dv01:,.0f}")

    scenario_output = {
        "name": scenario_name,
        "type": curve_shape,
        "base_curve": base_yield,
        "shocked_curve": shocked_yield,
        "tenors": key_tenors,
        "curve_bp_shift": curve_bp_shift,
        "dv01_estimate": total_dv01,
        "timestamp": datetime.now().isoformat()
    }

    # Load saved scenarios
    if "saved_scenarios" not in st.session_state:
        if os.path.exists("saved_scenarios.json"):
            with open("saved_scenarios.json", "r") as f:
                st.session_state.saved_scenarios = json.load(f)
        else:
            st.session_state.saved_scenarios = []

    st.markdown("---")
    st.subheader("Manage Saved Scenarios")

    col1, col2 = st.columns([1, 1])
    if col1.button("Save Scenario", disabled=not scenario_name.strip()):
        if scenario_name.strip() == "":
            st.error("Scenario Name cannot be empty.")
        else:
            # Check for duplicate names
            names = [s["name"] for s in st.session_state.saved_scenarios]
            if scenario_name in names:
                st.warning("Scenario with this name already exists.")
            else:
                st.session_state.saved_scenarios.append(scenario_output)
                with open("saved_scenarios.json", "w") as f:
                    json.dump(st.session_state.saved_scenarios, f)
                st.success(f"Saved scenario '{scenario_name}'.")

    if col2.button("Download CSV of Scenarios"):
        if st.session_state.saved_scenarios:
            csv_export = pd.DataFrame(st.session_state.saved_scenarios)
            csv_str = csv_export.to_csv(index=False)
            b64_csv = base64.b64encode(csv_str.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64_csv}" download="scenarios_export.csv">Download CSV</a>'
            st.markdown(href, unsafe_allow_html=True)
        else:
            st.info("No saved scenarios to export.")

    st.markdown("")

    # Show saved scenarios as a sortable table with actions
    if st.session_state.saved_scenarios:
        st.subheader("Saved Scenarios List")

        # Dataframe for display, add a 'Favorite' column if missing
        for s in st.session_state.saved_scenarios:
            s.setdefault("favorite", False)

        df_scenarios = pd.DataFrame(st.session_state.saved_scenarios)
        # Format timestamp nicely
        df_scenarios["timestamp"] = pd.to_datetime(df_scenarios["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
        df_scenarios["Favorite"] = df_scenarios["favorite"].apply(lambda x: "⭐" if x else "")
        df_display = df_scenarios[["name", "type", "dv01_estimate", "timestamp", "Favorite"]]
        df_display.columns = ["Name", "Type", "ΔMTM ($)", "Created At", "⭐"]

        # Sort by favorite then timestamp desc
        df_display = df_display.sort_values(by=["⭐", "Created At"], ascending=[False, False])
        st.dataframe(df_display, use_container_width=True)

        # Actions buttons for each scenario
        for i, s in enumerate(st.session_state.saved_scenarios):
            col1, col2, col3 = st.columns([1,1,1])
            with col1:
                if st.button(f"Delete '{s['name']}'", key=f"del_{i}"):
                    del st.session_state.saved_scenarios[i]
                    with open("saved_scenarios.json", "w") as f:
                        json.dump(st.session_state.saved_scenarios, f)
                    st.success(f"Deleted scenario '{s['name']}'.")
                    st.experimental_rerun()
            with col2:
                if not s["favorite"]:
                    if st.button(f"Mark Favorite '{s['name']}'", key=f"fav_{i}"):
                        st.session_state.saved_scenarios[i]["favorite"] = True
                        with open("saved_scenarios.json", "w") as f:
                            json.dump(st.session_state.saved_scenarios, f)
                        st.success(f"Marked '{s['name']}' as favorite.")
                        st.experimental_rerun()
                else:
                    if st.button(f"Unmark Favorite '{s['name']}'", key=f"unfav_{i}"):
                        st.session_state.saved_scenarios[i]["favorite"] = False
                        with open("saved_scenarios.json", "w") as f:
                            json.dump(st.session_state.saved_scenarios, f)
                        st.success(f"Unmarked '{s['name']}' as favorite.")
                        st.experimental_rerun()
            with col3:
                st.markdown("")  # placeholder for possible future actions

    else:
        st.info("No scenarios saved yet. Use the form above to create one.")

    st.markdown("---")
    st.caption("Scenario builder developed for ALM & Risk Quant portfolio showcasing.")

    return scenario_output
