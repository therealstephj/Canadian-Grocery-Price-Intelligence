"""SARIMA forecasts for the 8 staples, with rolling-origin validation (board card #21).

notebooks/forecasting.ipynb calls this module and walks through the results.
To rebuild the outputs without the notebook, run it directly from the repo root:
    python models/sarima/sarima.py

Method:
    - Model log(price), so errors are multiplicative and forecasts never go negative.
    - For each series and each training window, fit a small grid of SARIMA orders and
      keep the one with the lowest AIC. Nothing from the test year is used to choose.
    - Rolling-origin validation: three folds, each trained on everything before a
      12-month test year. The last fold (Oct 2025 to Sep 2026) is the same holdout as
      the seasonal-naive baseline (#20), so the numbers compare directly.
    - Final model: refit on all data and forecast the next 12 months with an 80% interval.

Outputs (in models/sarima):
    sarima_backtest.csv   every test month of every fold: actual, SARIMA, seasonal naive
    sarima_metrics.csv    MAE, RMSE, MAPE per series, fold and model
    sarima_forecasts.csv  next-12-month forecast per series, with 80% interval
"""
import sys
import warnings
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tools.sm_exceptions import ConvergenceWarning
from statsmodels.tsa.statespace.sarimax import SARIMAX

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "models" / "baseline"))
from seasonal_naive import KEYS, SEASON, load_prices  # noqa: E402  (shared data loading)

OUT = Path(__file__).resolve().parent
HORIZON = 12
# Each fold's test year starts the month after its cut-off.
FOLD_CUTOFFS = ["2023-09-01", "2024-09-01", "2025-09-01"]
MIN_TRAIN = 48  # months; shorter training windows are skipped

# Candidate (order, seasonal_order). Kept small: about 9 years of monthly data can't
# support much more, and a bigger search mostly overfits the training window.
# Every candidate uses the same differencing (d=1, D=0) because AIC is only comparable
# between models fitted to the same differenced series. A drift term ("t") lets the
# forecast keep rising, which is what retail prices have mostly done since 2017.
ORDERS = [(0, 1, 1), (1, 1, 0), (1, 1, 1), (2, 1, 0)]
SEASONAL = [(0, 0, 0, SEASON), (1, 0, 0, SEASON)]
GRID = [(o, s, "t") for o, s in product(ORDERS, SEASONAL)]


def fit_best(y):
    """Fit every candidate on log(y) and return (best fitted result, spec label)."""
    best, best_spec = None, None
    for order, seasonal, trend in GRID:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)
            warnings.simplefilter("ignore", UserWarning)
            try:
                res = SARIMAX(
                    np.log(y), order=order, seasonal_order=seasonal, trend=trend,
                    enforce_stationarity=True, enforce_invertibility=True,
                ).fit(disp=False)
            except (np.linalg.LinAlgError, ValueError):
                continue
        if np.isfinite(res.aic) and (best is None or res.aic < best.aic):
            best, best_spec = res, f"SARIMA{order}x{seasonal[:3]}{SEASON} trend={trend}"
    return best, best_spec


def forecast(res, steps, alpha=0.2):
    """Return a DataFrame with the forecast and its interval, back on the price scale."""
    fc = res.get_forecast(steps)
    ci = fc.conf_int(alpha=alpha)
    return pd.DataFrame({
        "forecast": np.exp(fc.predicted_mean),
        "lower_80": np.exp(ci.iloc[:, 0]),
        "upper_80": np.exp(ci.iloc[:, 1]),
    })


def score(actual, pred):
    err = actual - pred
    return {
        "mae": err.abs().mean(),
        "rmse": np.sqrt((err ** 2).mean()),
        "mape_pct": (err.abs() / actual).mean() * 100,
    }


def run(verbose=True):
    """Fit everything, write the three CSVs and return them as DataFrames."""
    prices = load_prices()
    backtest_rows, metric_rows, future_rows = [], [], []
    groups = list(prices.groupby(KEYS, sort=False))

    for i, (keys, group) in enumerate(groups, 1):
        label = dict(zip(KEYS, keys))
        y = group.set_index("date")["price"].asfreq("MS")
        if y.isna().any() or len(y) < MIN_TRAIN + HORIZON:
            continue  # territories and gappy series; same exclusions as the baseline
        if verbose:
            print(f"[{i:>2}/{len(groups)}] {label['province_code']} {label['product']}")

        for fold, cutoff in enumerate(FOLD_CUTOFFS, 1):
            train, test = y[:cutoff], y[cutoff:].iloc[1:HORIZON + 1]
            if len(test) < HORIZON or len(train) < MIN_TRAIN:
                continue
            res, spec = fit_best(train)
            if res is None:
                continue
            sarima = forecast(res, HORIZON)["forecast"].set_axis(test.index)
            naive = y.shift(SEASON).loc[test.index]  # price(t - 12), all from before the test year
            backtest_rows.append(pd.DataFrame({
                **label, "fold": fold, "date": test.index, "actual": test.values,
                "sarima": sarima.values, "seasonal_naive": naive.values, "spec": spec,
            }))
            for model, pred in [("sarima", sarima), ("seasonal_naive", naive)]:
                metric_rows.append({**label, "fold": fold, "test_start": test.index[0].date(),
                                    "model": model, **score(test, pred)})

        res, spec = fit_best(y)
        fc = forecast(res, HORIZON)
        fc.index = pd.date_range(y.index[-1] + pd.offsets.MonthBegin(), periods=HORIZON, freq="MS")
        future_rows.append(fc.rename_axis("date").reset_index().assign(**label, model="sarima", spec=spec))

    backtest = pd.concat(backtest_rows, ignore_index=True)
    metrics = pd.DataFrame(metric_rows)
    future = pd.concat(future_rows, ignore_index=True)[
        ["date", *KEYS, "model", "forecast", "lower_80", "upper_80", "spec"]]

    backtest.round({"actual": 2, "sarima": 2, "seasonal_naive": 2}).to_csv(
        OUT / "sarima_backtest.csv", index=False, date_format="%Y-%m-%d")
    metrics.round(3).to_csv(OUT / "sarima_metrics.csv", index=False)
    future.round({"forecast": 2, "lower_80": 2, "upper_80": 2}).to_csv(
        OUT / "sarima_forecasts.csv", index=False, date_format="%Y-%m-%d")
    if verbose:
        print(f"Wrote {len(future['product'].groupby([future['province_code'], future['product']]).size())}"
              " series to models/sarima/")
    return backtest, metrics, future


if __name__ == "__main__":
    run()
