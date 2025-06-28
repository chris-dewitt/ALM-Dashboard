import streamlit as st
import pandas as pd

def show():
    st.header("IRR/FX Derivatives Book")

    # Dummy example derivatives book
    data = {
        "Instrument": ["IRS", "Caps", "Swaptions", "FX Forward", "FX Swap"],
        "Notional ($)": [10000000, 5000000, 2000000, 3000000, 4000000],
        "Maturity (Months)": [60, 36, 24, 12, 6],
        "Type": ["Interest Rate", "Interest Rate", "Interest Rate", "FX", "FX"],
        "MTM ($)": [250000, 50000, 30000, 15000, 20000],
        "Delta": [0.8, 0.5, 0.6, 0.7, 0.65]
    }
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

    st.markdown("""
    This module provides a snapshot of the derivative positions in the IRR and FX books, with mark-to-market and delta exposure.
    """)

    total_notional = df["Notional ($)"].sum()
    total_mtm = df["MTM ($)"].sum()

    col1, col2 = st.columns(2)
    col1.metric("Total Notional", f"${total_notional:,.0f}")
    col2.metric("Total MTM", f"${total_mtm:,.0f}")

    st.bar_chart(df.set_index("Instrument")["MTM ($)"])
