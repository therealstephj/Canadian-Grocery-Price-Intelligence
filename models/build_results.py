"""Build models/results.csv, the forecast table for the dashboard (board card #23).

Usage (from the repo root, after the three models have written their outputs):
    python models/build_results.py

It reads the forecast and metric files from models/baseline, models/sarima and models/gbm
and doesn't refit anything. The column guide is in models/README.md.

One row per model, series (product x geography) and future month: 3 models x 87 series
x 12 months. The keys (date, province_code, product) match fact_price, so the table joins
to the same dimensions as the actual prices.
"""
import sys
from pathlib import Path

import pandas as pd

MODELS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(MODELS_DIR / "baseline"))
from seasonal_naive import KEYS, load_prices  # noqa: E402

OUT = MODELS_DIR / "results.csv"
HEADLINE = "gbm"  # the forecast the dashboard shows by default (see notebooks/forecasting.ipynb)
LABELS = {
    "gbm": "Gradient boosting",
    "sarima": "SARIMA",
    "seasonal_naive": "Seasonal naive (same month last year)",
}
COLUMNS = [
    "date", "province", "province_code", "product", "model", "model_label", "is_headline",
    "horizon_months", "forecast", "lower_80", "upper_80",
    "latest_date", "latest_price", "change_vs_latest_pct",
    "backtest_mae", "backtest_rmse", "backtest_mape_pct",
]


def load_forecasts():
    """Next-12-month forecasts from all three models, in one long table."""
    naive = pd.read_csv(MODELS_DIR / "baseline" / "baseline_forecasts.csv", parse_dates=["date"])
    naive = naive[naive["split"] == "future"][["date", *KEYS, "model", "forecast"]]
    sarima = pd.read_csv(MODELS_DIR / "sarima" / "sarima_forecasts.csv", parse_dates=["date"])
    gbm = pd.read_csv(MODELS_DIR / "gbm" / "gbm_forecasts.csv", parse_dates=["date"])
    cols = ["date", *KEYS, "model", "forecast", "lower_80", "upper_80"]
    # the seasonal-naive forecast has no interval; its lower/upper stay empty
    return pd.concat([naive, sarima[cols], gbm[cols]], ignore_index=True)


def load_accuracy():
    """Backtest error per model and series, averaged over the same three rolling folds.

    The seasonal-naive scores come from the SARIMA run, which scored it on all three folds.
    (models/baseline only scored the last fold.)
    """
    metrics = pd.concat([
        pd.read_csv(MODELS_DIR / "sarima" / "sarima_metrics.csv"),
        pd.read_csv(MODELS_DIR / "gbm" / "gbm_metrics.csv"),
    ])
    acc = metrics.groupby([*KEYS, "model"])[["mae", "rmse", "mape_pct"]].mean()
    return acc.add_prefix("backtest_").reset_index()


def main():
    forecasts = load_forecasts()
    prices = load_prices()
    latest = (prices.sort_values("date").groupby(KEYS).last().reset_index()
              .rename(columns={"date": "latest_date", "price": "latest_price"}))

    results = (forecasts
               .merge(latest, on=KEYS, how="left", validate="many_to_one")
               .merge(load_accuracy(), on=[*KEYS, "model"], how="left", validate="many_to_one"))
    results["model_label"] = results["model"].map(LABELS)
    results["is_headline"] = (results["model"] == HEADLINE).astype(int)
    results["horizon_months"] = (
        (results["date"].dt.year - results["latest_date"].dt.year) * 12
        + results["date"].dt.month - results["latest_date"].dt.month)
    results["change_vs_latest_pct"] = (results["forecast"] / results["latest_price"] - 1) * 100

    results = results[COLUMNS].sort_values(["model", "province_code", "product", "date"])
    check(results)
    results = results.round({
        "forecast": 2, "lower_80": 2, "upper_80": 2, "latest_price": 2, "change_vs_latest_pct": 1,
        "backtest_mae": 3, "backtest_rmse": 3, "backtest_mape_pct": 2,
    })
    results.to_csv(OUT, index=False, date_format="%Y-%m-%d")

    n_series = results.groupby(KEYS).ngroups
    print(f"Wrote {len(results):,} rows to models/results.csv "
          f"({results['model'].nunique()} models x {n_series} series x 12 months)")


def check(results):
    """Stop with a clear message if the table isn't what the dashboard expects."""
    problems = []
    if results.duplicated(["date", "province_code", "product", "model"]).any():
        problems.append("duplicate (date, province_code, product, model) rows")
    sizes = results.groupby(["model", *KEYS]).size()
    if (sizes != 12).any():
        problems.append(f"{(sizes != 12).sum()} model/series pairs without exactly 12 months")
    per_model = results.groupby("model").apply(lambda g: g.groupby(KEYS).ngroups, include_groups=False)
    if per_model.nunique() != 1:
        problems.append(f"models cover different series: {per_model.to_dict()}")
    needed = ["forecast", "latest_price", "backtest_mape_pct", "model_label"]
    if results[needed].isna().any().any():
        problems.append(f"missing values in {results[needed].columns[results[needed].isna().any()].tolist()}")
    if not results["horizon_months"].between(1, 12).all():
        problems.append("horizon outside 1..12")
    has_interval = results["model"] != "seasonal_naive"
    bad = has_interval & ~((results["lower_80"] <= results["forecast"]) & (results["forecast"] <= results["upper_80"]))
    if bad.any():
        problems.append(f"{bad.sum()} rows where the forecast is outside its own interval")
    if problems:
        raise SystemExit("results.csv failed its checks:\n  - " + "\n  - ".join(problems))


if __name__ == "__main__":
    main()
