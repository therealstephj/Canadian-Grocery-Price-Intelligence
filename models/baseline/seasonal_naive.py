"""Seasonal-naive baseline forecast for the 8 agreed staples (board card #20).

The forecast for any month is the price in the same month one year earlier:
    forecast(t) = price(t - 12)
Every later model (#21, #22) must beat this baseline's MAE and RMSE to be worth using.

Usage (from the repo root):
    python models/baseline/seasonal_naive.py

Input:
    data/clean/prices_clean.csv if it exists (shared schema columns), otherwise
    data/raw/18100245_prices.csv, mapped to the shared schema names in this script.

Outputs (in models/baseline):
    baseline_forecasts.csv  one row per series and month: backtest months (actual vs forecast)
                            and the next 12 months (forecast only)
    baseline_metrics.csv    MAE, RMSE and MAPE per series on the 12-month holdout

Method:
    Holdout = the last 12 months of data. The forecast for each holdout month uses only
    data from before the holdout. Series with fewer than 24 months (12 to look back on,
    12 to test) are skipped and listed when the script runs.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CLEAN = ROOT / "data" / "clean" / "prices_clean.csv"
RAW = ROOT / "data" / "raw" / "18100245_prices.csv"
OUT = Path(__file__).resolve().parent

SEASON = 12   # months in a season
HORIZON = 12  # holdout length and future forecast length, in months

# Agreed in week 1 (docs/shared_schema.md, decision 5).
STAPLES = [
    "Ground beef, per kilogram",
    "Chicken breasts, per kilogram",
    "Eggs, 1 dozen",
    "Milk, 4 litres",
    "Butter, 454 grams",
    "White bread, 675 grams",
    "Roasted or ground coffee, 340 grams",
    "Bananas, per kilogram",
]

# Raw GEO -> (province, province_code), from docs/shared_schema.md decision 1.
GEOGRAPHY = {
    "Canada": ("Canada", "CA"),
    "Newfoundland and Labrador": ("Newfoundland and Labrador", "NL"),
    "Prince Edward Island": ("Prince Edward Island", "PE"),
    "Nova Scotia": ("Nova Scotia", "NS"),
    "New Brunswick": ("New Brunswick", "NB"),
    "Quebec": ("Quebec", "QC"),
    "Ontario": ("Ontario", "ON"),
    "Manitoba": ("Manitoba", "MB"),
    "Saskatchewan": ("Saskatchewan", "SK"),
    "Alberta": ("Alberta", "AB"),
    "British Columbia": ("British Columbia", "BC"),
    "Whitehorse, Yukon": ("Yukon", "YT"),
    "Yellowknife, Northwest Territories": ("Northwest Territories", "NT"),
}

KEYS = ["province", "province_code", "product"]


def load_prices():
    """Return staple prices with columns date, province, province_code, product, price."""
    if CLEAN.exists():
        df = pd.read_csv(CLEAN, parse_dates=["date"])
        source = CLEAN
    else:
        raw = pd.read_csv(RAW, usecols=["REF_DATE", "GEO", "Products", "VALUE"])
        raw = raw[raw["GEO"].isin(GEOGRAPHY)]
        df = pd.DataFrame({
            "date": pd.to_datetime(raw["REF_DATE"] + "-01"),
            "province": raw["GEO"].map(lambda g: GEOGRAPHY[g][0]),
            "province_code": raw["GEO"].map(lambda g: GEOGRAPHY[g][1]),
            "product": raw["Products"],
            "price": raw["VALUE"],
        })
        source = RAW
    df = df[df["product"].isin(STAPLES)].dropna(subset=["price"])
    missing = set(STAPLES) - set(df["product"])
    if missing:
        raise SystemExit(f"Staples not found in {source}: {sorted(missing)}")
    print(f"Read {len(df):,} staple prices from {source.relative_to(ROOT)}")
    return df[["date", *KEYS, "price"]].sort_values([*KEYS, "date"])


def forecast_series(s):
    """Backtest and future forecast for one monthly price series (indexed by date).

    Returns (rows, metrics) or None if the series is too short or has gaps.
    """
    s = s.asfreq("MS")  # makes any missing month an explicit NaN
    if len(s) < SEASON + HORIZON or s.iloc[-(SEASON + HORIZON):].isna().any():
        return None

    test = s.iloc[-HORIZON:]
    # price(t - 12) for every holdout month; with HORIZON <= SEASON these all lie before the holdout
    backtest = s.shift(SEASON).iloc[-HORIZON:]
    error = test - backtest

    future_dates = pd.date_range(s.index[-1] + pd.offsets.MonthBegin(), periods=HORIZON, freq="MS")
    # the future month t uses price(t - 12), i.e. the last 12 observed months, repeated
    future = pd.Series(s.iloc[-SEASON:].to_numpy()[np.arange(HORIZON) % SEASON], index=future_dates)

    rows = pd.concat([
        pd.DataFrame({"date": test.index, "split": "backtest", "actual": test.values, "forecast": backtest.values}),
        pd.DataFrame({"date": future.index, "split": "future", "actual": np.nan, "forecast": future.values}),
    ])
    metrics = {
        "holdout_start": test.index[0].date(),
        "holdout_end": test.index[-1].date(),
        "n_months": len(test),
        "mae": error.abs().mean(),
        "rmse": np.sqrt((error ** 2).mean()),
        "mape_pct": (error.abs() / test).mean() * 100,
        "mean_actual": test.mean(),
    }
    return rows, metrics


def main():
    prices = load_prices()
    all_rows, all_metrics, skipped = [], [], []

    for keys, group in prices.groupby(KEYS, sort=False):
        result = forecast_series(group.set_index("date")["price"])
        label = dict(zip(KEYS, keys))
        if result is None:
            skipped.append(f"{label['product']} / {label['province']} ({len(group)} months)")
            continue
        rows, metrics = result
        all_rows.append(rows.assign(**label))
        all_metrics.append({**label, **metrics})

    forecasts = pd.concat(all_rows)[["date", *KEYS, "split", "actual", "forecast"]]
    forecasts.insert(len(KEYS) + 2, "model", "seasonal_naive")
    metrics = pd.DataFrame(all_metrics)
    metrics.insert(len(KEYS), "model", "seasonal_naive")

    forecasts[["actual", "forecast"]] = forecasts[["actual", "forecast"]].round(2)
    forecasts.to_csv(OUT / "baseline_forecasts.csv", index=False, date_format="%Y-%m-%d")
    metrics.round(3).to_csv(OUT / "baseline_metrics.csv", index=False)

    print(f"Forecast {len(metrics)} series; wrote baseline_forecasts.csv and baseline_metrics.csv")
    if skipped:
        print(f"Skipped {len(skipped)} series (need {SEASON + HORIZON} complete recent months):")
        for item in skipped:
            print(f"  - {item}")

    canada = metrics[metrics["province_code"] == "CA"].set_index("product")
    print("\nCanada, 12-month holdout:")
    print(canada[["mae", "rmse", "mape_pct", "mean_actual"]].round(2).to_string())


if __name__ == "__main__":
    main()
