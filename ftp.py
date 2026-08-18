import pandas as pd
import plotly.graph_objs as go
import streamlit as st


DEFAULT_FTP_CURVE = {
    12: 1.0,
    24: 1.5,
    36: 2.0,
    60: 2.5,
    84: 3.0,
    120: 3.5,
}


def map_ftp_rate(months: float, ftp_curve: dict | None = None) -> float:
    curve = ftp_curve or DEFAULT_FTP_CURVE
    for maturity, rate in sorted(curve.items()):
        if months <= maturity:
            return rate
    return max(curve.values())


def build_ftp_table(balance_sheet: pd.DataFrame, ftp_curve: dict | None = None) -> pd.DataFrame:
    ftp_df = balance_sheet.copy()
    ftp_df["FTP Rate (%)"] = ftp_df["Maturity (Months)"].apply(
        lambda m: map_ftp_rate(m, ftp_curve)
    )
    ftp_df["FTP Charge ($)"] = ftp_df["Amount ($)"] * ftp_df["FTP Rate (%)"] / 100
    ftp_df["FTP Net ($)"] = (
        ftp_df["Amount ($)"] * (ftp_df["Rate (%)"] - ftp_df["FTP Rate (%)"]) / 100
    )
    return ftp_df


def show(balance_sheet):
    st.header("Funds Transfer Pricing")
    st.caption(
        "Match-funded FTP rates by maturity with product-level net interest contribution."
    )

    ftp_df = build_ftp_table(balance_sheet)

    st.dataframe(
        ftp_df[
            [
                "Product",
                "Type",
                "Amount ($)",
                "Rate (%)",
                "FTP Rate (%)",
                "FTP Net ($)",
            ]
        ].style.format(
            {
                "Amount ($)": "${:,.0f}",
                "Rate (%)": "{:.2f}",
                "FTP Rate (%)": "{:.2f}",
                "FTP Net ($)": "${:,.0f}",
            }
        ),
        use_container_width=True,
    )

    total_ftp = float(ftp_df["FTP Net ($)"].sum())
    asset_ftp = float(ftp_df.loc[ftp_df["Type"] == "Asset", "FTP Net ($)"].sum())
    liability_ftp = float(ftp_df.loc[ftp_df["Type"] == "Liability", "FTP Net ($)"].sum())

    col1, col2, col3 = st.columns(3)
    col1.metric("Total FTP Net", f"${total_ftp:,.0f}")
    col2.metric("Asset Contribution", f"${asset_ftp:,.0f}")
    col3.metric("Liability Contribution", f"${liability_ftp:,.0f}")

    product_fig = go.Figure(
        data=[
            go.Bar(
                x=ftp_df["Product"],
                y=ftp_df["FTP Net ($)"],
                marker_color=[
                    "#2E86AB" if t == "Asset" else "#E94F37" for t in ftp_df["Type"]
                ],
                name="FTP Net",
            )
        ]
    )
    product_fig.update_layout(
        title="FTP Net Contribution by Product",
        yaxis_title="FTP Net ($)",
        xaxis_title="Product",
    )
    st.plotly_chart(product_fig, use_container_width=True)

    summary = ftp_df.groupby("Type", observed=False)["FTP Net ($)"].sum()
    type_fig = go.Figure(
        data=[go.Bar(x=summary.index.astype(str), y=summary.values, name="FTP Net")]
    )
    type_fig.update_layout(title="FTP Contribution by Type", yaxis_title="FTP Net ($)")
    st.plotly_chart(type_fig, use_container_width=True)
