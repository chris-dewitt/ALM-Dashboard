import streamlit as st
import pandas as pd

def show(balance_sheet):
    st.header("Funds Transfer Pricing")

    ftp_df = balance_sheet.copy()
    ftp_curve = {
        12: 1.0,
        24: 1.5,
        36: 2.0,
        60: 2.5,
        84: 3.0,
        120: 3.5
    }

    def map_ftp_rate(months):
        for m in sorted(ftp_curve):
            if months <= m:
                return ftp_curve[m]
        return max(ftp_curve.values())

    ftp_df["FTP Rate"] = ftp_df["Maturity (Months)"].apply(map_ftp_rate)
    ftp_df["FTP Charge ($)"] = ftp_df["Amount ($)"] * ftp_df["FTP Rate"] / 100
    ftp_df["FTP Net ($)"] = ftp_df["Amount ($)"] * (ftp_df["Rate (%)"] - ftp_df["FTP Rate"]) / 100

    st.dataframe(ftp_df[["Product", "Type", "Amount ($)", "Rate (%)", "FTP Rate", "FTP Net ($)"]], use_container_width=True)

    ftp_summary = ftp_df.groupby("Type")["FTP Net ($)"].sum()
    st.subheader("FTP Contribution by Type")
    st.bar_chart(ftp_summary)
