"""Shared helpers for ALM Dashboard analytics modules."""

from __future__ import annotations

from typing import Iterable, Sequence

import pandas as pd

REQUIRED_COLUMNS = [
    "Product",
    "Type",
    "Amount ($)",
    "Rate (%)",
    "Duration (Years)",
    "Maturity (Months)",
]

NUMERIC_COLUMNS = ["Amount ($)", "Rate (%)", "Duration (Years)", "Maturity (Months)"]

MATURITY_BINS_STANDARD = [0, 1, 3, 6, 12, 24, 36, 60, float("inf")]
MATURITY_LABELS_STANDARD = ["0-1M", "1-3M", "3-6M", "6-12M", "1-2Y", "2-3Y", "3-5Y", ">5Y"]

MATURITY_BINS_EXTENDED = [0, 1, 3, 6, 12, 24, 36, 60, 120, float("inf")]
MATURITY_LABELS_EXTENDED = [
    "0-1M",
    "1-3M",
    "3-6M",
    "6-12M",
    "1-2Y",
    "2-3Y",
    "3-5Y",
    "5-10Y",
    ">10Y",
]

CURRENCY_FORMAT = "${:,.0f}"
PERCENT_FORMAT = "{:.2f}%"
RATE_FORMAT = "{:.2f}"


def validate_balance_sheet(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and coerce an uploaded or sample balance sheet dataframe."""
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    validated_df = df[REQUIRED_COLUMNS].copy()

    for col in NUMERIC_COLUMNS:
        validated_df[col] = pd.to_numeric(validated_df[col], errors="coerce")

    if validated_df[NUMERIC_COLUMNS].isna().any().any():
        raise ValueError("One or more numeric columns contains blank or non-numeric values.")

    allowed_types = {"Asset", "Liability"}
    invalid_types = sorted(set(validated_df["Type"]) - allowed_types)
    if invalid_types:
        raise ValueError("Type must be either 'Asset' or 'Liability'.")

    if (validated_df["Amount ($)"] < 0).any():
        raise ValueError("Amount ($) values must be non-negative.")

    if (validated_df["Maturity (Months)"] < 0).any():
        raise ValueError("Maturity (Months) values must be non-negative.")

    if (validated_df["Duration (Years)"] < 0).any():
        raise ValueError("Duration (Years) values must be non-negative.")

    return validated_df


def assign_maturity_bucket(
    series: pd.Series,
    bins: Sequence[float] | None = None,
    labels: Sequence[str] | None = None,
) -> pd.Series:
    """Bucket remaining maturity (months) into standard ALM time bands."""
    use_bins = list(bins) if bins is not None else MATURITY_BINS_STANDARD
    use_labels = list(labels) if labels is not None else MATURITY_LABELS_STANDARD
    return pd.cut(
        series,
        bins=use_bins,
        labels=use_labels,
        right=True,
        include_lowest=True,
    )


def weighted_average(values: pd.Series, weights: pd.Series) -> float:
    """Return the weight-weighted average of *values*."""
    total_weight = float(weights.sum())
    if total_weight == 0:
        return 0.0
    return float((values * weights).sum() / total_weight)


def format_currency_columns(df: pd.DataFrame, columns: Iterable[str]):
    """Apply standard currency formatting to selected dataframe columns."""
    fmt = {col: CURRENCY_FORMAT for col in columns if col in df.columns}
    return df.style.format(fmt)


def summarize_balance_sheet(df: pd.DataFrame) -> dict:
    """Compute high-level balance sheet KPIs used on the Overview page."""
    assets = df.loc[df["Type"] == "Asset"]
    liabilities = df.loc[df["Type"] == "Liability"]

    total_assets = float(assets["Amount ($)"].sum())
    total_liabilities = float(liabilities["Amount ($)"].sum())
    equity = total_assets - total_liabilities

    asset_yield = weighted_average(assets["Rate (%)"], assets["Amount ($)"])
    liability_cost = weighted_average(liabilities["Rate (%)"], liabilities["Amount ($)"])
    asset_duration = weighted_average(assets["Duration (Years)"], assets["Amount ($)"])
    liability_duration = weighted_average(
        liabilities["Duration (Years)"], liabilities["Amount ($)"]
    )

    return {
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "equity": equity,
        "equity_ratio": (equity / total_assets * 100) if total_assets else 0.0,
        "asset_yield": asset_yield,
        "liability_cost": liability_cost,
        "net_interest_spread": asset_yield - liability_cost,
        "asset_duration": asset_duration,
        "liability_duration": liability_duration,
        "simple_duration_gap": asset_duration - liability_duration,
    }


def calculate_duration_gap(df: pd.DataFrame) -> dict:
    """
    Calculate classic ALM duration gap metrics.

    Duration Gap = DA - (L / A) * DL

    where DA and DL are market-value-weighted average durations of assets
    and liabilities, A is total assets, and L is total liabilities.
    """
    assets = df.loc[df["Type"] == "Asset"]
    liabilities = df.loc[df["Type"] == "Liability"]

    total_assets = float(assets["Amount ($)"].sum())
    total_liabilities = float(liabilities["Amount ($)"].sum())

    if total_assets == 0:
        raise ValueError("Total assets are zero; cannot calculate duration gap.")
    if total_liabilities == 0:
        raise ValueError("Total liabilities are zero; cannot calculate duration gap.")

    da = weighted_average(assets["Duration (Years)"], assets["Amount ($)"])
    dl = weighted_average(liabilities["Duration (Years)"], liabilities["Amount ($)"])
    leverage = total_liabilities / total_assets
    duration_gap = da - leverage * dl

    return {
        "weighted_avg_asset_duration": da,
        "weighted_avg_liability_duration": dl,
        "leverage_ratio": leverage,
        "duration_gap": duration_gap,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
    }


def estimate_eve_change(duration_gap: float, total_assets: float, rate_shock_bps: float) -> float:
    """Approximate ΔEVE ≈ -Duration Gap × A × Δr for a parallel rate shock."""
    return -duration_gap * total_assets * (rate_shock_bps / 10000.0)
