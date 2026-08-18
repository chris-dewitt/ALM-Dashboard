"""Unit tests for ALM Dashboard calculation helpers."""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import pytest

from alm_utils import (
    assign_maturity_bucket,
    calculate_duration_gap,
    estimate_eve_change,
    summarize_balance_sheet,
    weighted_average,
)
from ftp import build_ftp_table, map_ftp_rate
from irr import calc_eve, calc_nii
from scenario_builder import build_shocked_curve

SAMPLE_CSV = Path(__file__).resolve().parents[1] / "data" / "sample_balance_sheet.csv"


@pytest.fixture
def sample_balance_sheet() -> pd.DataFrame:
    return pd.read_csv(SAMPLE_CSV)


def test_weighted_average_basic():
    values = pd.Series([1.0, 3.0])
    weights = pd.Series([1.0, 1.0])
    assert weighted_average(values, weights) == pytest.approx(2.0)


def test_weighted_average_zero_weight():
    assert weighted_average(pd.Series([1.0]), pd.Series([0.0])) == 0.0


def test_assign_maturity_bucket_labels(sample_balance_sheet):
    buckets = assign_maturity_bucket(sample_balance_sheet["Maturity (Months)"])
    assert "6-12M" in set(buckets.astype(str))
    assert ">5Y" in set(buckets.astype(str))


def test_summarize_balance_sheet(sample_balance_sheet):
    kpis = summarize_balance_sheet(sample_balance_sheet)
    assert kpis["total_assets"] == pytest.approx(18_400_000)
    assert kpis["total_liabilities"] == pytest.approx(12_800_000)
    assert kpis["equity"] == pytest.approx(5_600_000)
    assert kpis["equity_ratio"] == pytest.approx(30.4347826, rel=1e-4)
    assert kpis["net_interest_spread"] > 0


def test_duration_gap_uses_leverage_adjustment(sample_balance_sheet):
    metrics = calculate_duration_gap(sample_balance_sheet)
    da = metrics["weighted_avg_asset_duration"]
    dl = metrics["weighted_avg_liability_duration"]
    leverage = metrics["leverage_ratio"]

    assert metrics["duration_gap"] == pytest.approx(da - leverage * dl)
    assert leverage == pytest.approx(12_800_000 / 18_400_000)
    # Corrected gap should differ from the naive DA - DL shortcut.
    assert metrics["duration_gap"] != pytest.approx(da - dl)


def test_estimate_eve_change_sign():
    # Positive duration gap + rate up => EVE down
    assert estimate_eve_change(1.5, 10_000_000, 100) == pytest.approx(-150_000)


def test_map_ftp_rate_boundaries():
    assert map_ftp_rate(12) == 1.0
    assert map_ftp_rate(13) == 1.5
    assert map_ftp_rate(200) == 3.5


def test_build_ftp_table(sample_balance_sheet):
    ftp_df = build_ftp_table(sample_balance_sheet)
    assert "FTP Rate (%)" in ftp_df.columns
    assert "FTP Net ($)" in ftp_df.columns
    assert len(ftp_df) == len(sample_balance_sheet)


def test_calc_nii_zero_shift(sample_balance_sheet):
    sensitivity = {product: 0.0 for product in sample_balance_sheet["Product"]}
    nii = calc_nii(sample_balance_sheet, 0.0, sensitivity)
    assets = sample_balance_sheet.loc[sample_balance_sheet["Type"] == "Asset"]
    liabs = sample_balance_sheet.loc[sample_balance_sheet["Type"] == "Liability"]
    expected = (assets["Amount ($)"] * assets["Rate (%)"] / 100).sum() - (
        liabs["Amount ($)"] * liabs["Rate (%)"] / 100
    ).sum()
    assert nii == pytest.approx(expected)


def test_calc_eve_duration_shock(sample_balance_sheet):
    base = calc_eve(sample_balance_sheet, 0.0)
    up = calc_eve(sample_balance_sheet, 1.0)  # +100 bps expressed as percent points
    # With positive duration gap, EVE should fall when rates rise.
    assert up < base


def test_build_shocked_curve_parallel():
    shocked = build_shocked_curve("Parallel Shift", shift_bps=100)
    assert shocked == pytest.approx([3.0, 3.1, 3.4, 3.8, 4.2])


def test_validate_balance_sheet_rejects_bad_type():
    from alm_utils import validate_balance_sheet

    bad = pd.read_csv(
        io.StringIO(
            "Product,Type,Amount ($),Rate (%),Duration (Years),Maturity (Months)\n"
            "X,Equity,100,1,1,12\n"
        )
    )
    with pytest.raises(ValueError, match="Asset' or 'Liability"):
        validate_balance_sheet(bad)
