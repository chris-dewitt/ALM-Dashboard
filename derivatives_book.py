import pandas as pd
import plotly.graph_objs as go
import streamlit as st


SAMPLE_DERIVATIVES = {
    "Instrument": ["IRS", "Caps", "Swaptions", "FX Forward", "FX Swap"],
    "Notional ($)": [10_000_000, 5_000_000, 2_000_000, 3_000_000, 4_000_000],
    "Maturity (Months)": [60, 36, 24, 12, 6],
    "Type": ["Interest Rate", "Interest Rate", "Interest Rate", "FX", "FX"],
    "MTM ($)": [250_000, 50_000, 30_000, 15_000, 20_000],
    "Delta": [0.8, 0.5, 0.6, 0.7, 0.65],
}


def build_derivatives_book(data: dict | None = None) -> pd.DataFrame:
    df = pd.DataFrame(data or SAMPLE_DERIVATIVES)
    df["Delta Notional ($)"] = df["Notional ($)"] * df["Delta"]
    return df


def show():
    st.header("IRR/FX Derivatives Book")
    st.caption(
        "Sample interest-rate and FX derivative exposures with mark-to-market and delta notional."
    )

    df = build_derivatives_book()

    st.dataframe(
        df.style.format(
            {
                "Notional ($)": "${:,.0f}",
                "MTM ($)": "${:,.0f}",
                "Delta": "{:.2f}",
                "Delta Notional ($)": "${:,.0f}",
            }
        ),
        use_container_width=True,
    )

    total_notional = float(df["Notional ($)"].sum())
    total_mtm = float(df["MTM ($)"].sum())
    total_delta_notional = float(df["Delta Notional ($)"].sum())

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Notional", f"${total_notional:,.0f}")
    col2.metric("Total MTM", f"${total_mtm:,.0f}")
    col3.metric("Delta Notional", f"${total_delta_notional:,.0f}")

    mtm_fig = go.Figure(
        data=[
            go.Bar(
                x=df["Instrument"],
                y=df["MTM ($)"],
                marker_color=[
                    "#2E86AB" if t == "Interest Rate" else "#F6AE2D" for t in df["Type"]
                ],
                name="MTM",
            )
        ]
    )
    mtm_fig.update_layout(title="Mark-to-Market by Instrument", yaxis_title="MTM ($)")
    st.plotly_chart(mtm_fig, use_container_width=True)

    type_summary = df.groupby("Type", observed=False)[["Notional ($)", "MTM ($)"]].sum()
    type_fig = go.Figure()
    type_fig.add_trace(
        go.Bar(name="Notional", x=type_summary.index, y=type_summary["Notional ($)"])
    )
    type_fig.add_trace(
        go.Bar(name="MTM", x=type_summary.index, y=type_summary["MTM ($)"])
    )
    type_fig.update_layout(
        barmode="group",
        title="Exposure Summary by Asset Class",
        yaxis_title="USD",
    )
    st.plotly_chart(type_fig, use_container_width=True)

    st.markdown(
        "Illustrative book only — valuations and Greeks are placeholders for portfolio demonstration."
    )
