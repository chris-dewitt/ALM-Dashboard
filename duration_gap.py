import plotly.graph_objs as go
import streamlit as st

from alm_utils import calculate_duration_gap, estimate_eve_change


def show(balance_sheet):
    st.header("Duration Gap Analysis")
    st.caption(
        "Classic ALM duration gap: DA − (L/A) × DL, with approximate equity-value sensitivity."
    )

    if "Duration (Years)" not in balance_sheet.columns:
        st.error("Duration column missing from balance sheet data.")
        return

    try:
        metrics = calculate_duration_gap(balance_sheet)
    except ValueError as exc:
        st.error(str(exc))
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Weighted Avg Asset Duration",
        f"{metrics['weighted_avg_asset_duration']:.2f} yrs",
    )
    col2.metric(
        "Weighted Avg Liability Duration",
        f"{metrics['weighted_avg_liability_duration']:.2f} yrs",
    )
    col3.metric("Leverage (L/A)", f"{metrics['leverage_ratio']:.2%}")
    col4.metric("Duration Gap", f"{metrics['duration_gap']:.2f} yrs")

    shock_bps = st.slider("Parallel rate shock (bps)", -300, 300, 100, 25)
    eve_change = estimate_eve_change(
        metrics["duration_gap"],
        metrics["total_assets"],
        shock_bps,
    )
    st.metric(
        f"Estimated ΔEVE at {shock_bps:+d} bps",
        f"${eve_change:,.0f}",
        help="Approximation: ΔEVE ≈ −Duration Gap × Assets × Δr",
    )

    if metrics["duration_gap"] > 0:
        st.info(
            "Positive duration gap: equity value tends to fall when rates rise "
            "and rise when rates fall (asset-sensitive book)."
        )
    elif metrics["duration_gap"] < 0:
        st.info(
            "Negative duration gap: equity value tends to rise when rates rise "
            "and fall when rates fall (liability-sensitive book)."
        )
    else:
        st.success("Duration gap is near zero: book is approximately duration-matched.")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=["Assets (DA)", "Liabilities (DL)", "Duration Gap"],
            y=[
                metrics["weighted_avg_asset_duration"],
                metrics["weighted_avg_liability_duration"],
                metrics["duration_gap"],
            ],
            marker_color=["#2E86AB", "#E94F37", "#F6AE2D"],
            name="Duration",
        )
    )
    fig.update_layout(
        title="Duration Profile and Gap",
        yaxis_title="Duration (Years)",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Duration Gap = DA − (L/A) × DL. This educational approximation ignores "
        "convexity, behavioral options, and basis risk."
    )
