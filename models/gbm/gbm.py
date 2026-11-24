"""Gradient boosting with lag features for the 8 staples (board card #22).

notebooks/forecasting.ipynb calls this module and compares it with SARIMA (#21) and the
seasonal-naive baseline (#20). To rebuild the outputs without the notebook:
    python models/gbm/gbm.py

Method:
    - One global model for all 87 series, so each staple learns from every province.
    - Direct multi-horizon forecasting. Each training row is (origin month T, horizon h):
      the features use only prices up to T, and the target is the log change
      log(price[T+h]) - log(price[T]) for h = 1..12. Predicting a change rather than a
      price lets the trees, which can't extrapolate, still work for prices above
      anything seen in training.
    - Features: horizon, the target's calendar month, product and province (categorical),
      recent log changes (1, 2, 3, 6 and 12 months), 3- and 12-month volatility, and the
      seasonal signal: the change from T to the same calendar month a year before T+h.
    - Three quantile models (10th, 50th and 90th percentile). The median is the forecast;
      the other two give an 80% interval.
    - Same three rolling folds as SARIMA. For each fold, training rows only use targets
      dated on or before the cut-off, so no test-year price leaks in.
    - Hyperparameters are fixed up front (below), not tuned on the test folds.

Outputs (in models/gbm):
    gbm_backtest.csv   every test month of every fold: actual, forecast and 80% interval
    gbm_metrics.csv    MAE, RMSE, MAPE per series and fold
    gbm_forecasts.csv  next-12-month forecast per series, with 80% interval
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "models" / "baseline"))
sys.path.insert(0, str(ROOT / "models" / "sarima"))
from seasonal_naive import KEYS, load_prices  # noqa: E402
from sarima import FOLD_CUTOFFS, HORIZON, score  # noqa: E402  (same folds as SARIMA)

OUT = Path(__file__).resolve().parent
LAGS = [1, 2, 3, 6, 12]
QUANTILES = {"lower_80": 0.1, "forecast": 0.5, "upper_80": 0.9}
PARAMS = dict(
    learning_rate=0.05, max_iter=300, max_leaf_nodes=15, min_samples_leaf=40,
    l2_regularization=1.0, categorical_features=["product", "province_code"], random_state=0,
)
FEATURES = ["h", "target_month", "product", "province_code",
            *[f"chg_{k}" for k in LAGS], "vol_3", "vol_12", "seasonal_chg"]


def complete_series(prices):
    """Wide log-price table (months x series), keeping only series with no gaps.

    Same exclusions as the baseline and SARIMA: territories (data starts Sep 2025)
    and anything else with missing months.
    """
    wide = prices.pivot_table(index="date", columns=KEYS, values="price").asfreq("MS")
    keep = wide.columns[wide.notna().all()]
    return np.log(wide[keep])


def make_rows(logp, origins):
    """Feature rows for every series, origin month in `origins` and horizon 1..12.

    Targets beyond the last month of `logp` are left as NaN (used for the future forecast).
    """
    diff1 = logp.diff()
    feats = {f"chg_{k}": logp - logp.shift(k) for k in LAGS}
    feats["vol_3"] = diff1.rolling(3).std()
    feats["vol_12"] = diff1.rolling(12).std()

    frames = []
    for h in range(1, HORIZON + 1):
        # target month T+h; the same month one year earlier is T+h-12, which is <= T
        seasonal = logp.shift(12 - h) - logp
        target = logp.shift(-h) - logp
        parts = {name: f.loc[origins] for name, f in feats.items()}
        parts["seasonal_chg"] = seasonal.loc[origins]
        parts["target"] = target.loc[origins]
        df = pd.concat({k: v.stack(KEYS, future_stack=True) for k, v in parts.items()}, axis=1)
        df = df.reset_index().rename(columns={"date": "origin"})
        df["h"] = h
        frames.append(df)

    rows = pd.concat(frames, ignore_index=True)
    rows["target_date"] = (rows["origin"].dt.to_period("M") + rows["h"]).dt.to_timestamp()
    rows["target_month"] = rows["target_date"].dt.month
    for col in ["product", "province_code"]:
        rows[col] = rows[col].astype("category")
    return rows


def last_price(logp, month, rows):
    """Price at `month` for each row's series, aligned to `rows`."""
    lp = np.exp(logp.loc[month]).rename("last").reset_index()
    return rows[KEYS].astype(str).merge(lp, on=KEYS, how="left")["last"].to_numpy()


def fit_predict(train, test):
    """Fit the three quantile models on `train` and predict log changes for `test`."""
    train = train.dropna(subset=FEATURES + ["target"])
    preds = {}
    for name, q in QUANTILES.items():
        model = HistGradientBoostingRegressor(loss="quantile", quantile=q, **PARAMS)
        model.fit(train[FEATURES], train["target"])
        preds[name] = model.predict(test[FEATURES])
    out = pd.DataFrame(preds, index=test.index)
    # keep the interval ordered even where the separate quantile models cross
    out["lower_80"] = np.minimum(out["lower_80"], out["forecast"])
    out["upper_80"] = np.maximum(out["upper_80"], out["forecast"])
    return out


def run(verbose=True):
    prices = load_prices()
    logp = complete_series(prices)
    dates = logp.index
    all_rows = make_rows(logp, dates)
    # categories must match between train and test; take them from the full set
    cats = {c: all_rows[c].cat.categories for c in ["product", "province_code"]}

    backtest_rows, metric_rows = [], []
    for fold, cutoff in enumerate(FOLD_CUTOFFS, 1):
        cutoff = pd.Timestamp(cutoff)
        train = all_rows[all_rows["target_date"] <= cutoff]  # targets known by the cut-off
        test = all_rows[all_rows["origin"] == cutoff]
        pred = fit_predict(train, test)
        last = last_price(logp, cutoff, test)
        res = test[[*KEYS, "target_date"]].assign(
            fold=fold,
            actual=np.exp(test["target"]) * last,
            gbm=np.exp(pred["forecast"]) * last,
            lower_80=np.exp(pred["lower_80"]) * last,
            upper_80=np.exp(pred["upper_80"]) * last,
        ).rename(columns={"target_date": "date"})
        backtest_rows.append(res)
        for keys, g in res.groupby(KEYS, observed=True):
            metric_rows.append({**dict(zip(KEYS, keys)), "fold": fold, "test_start": g["date"].min().date(),
                                "model": "gbm", **score(g["actual"], g["gbm"])})
        if verbose:
            print(f"fold {fold}: trained on {len(train):,} rows, test year from {res['date'].min():%Y-%m}")

    # final model: every row whose target is known, forecast from the last month
    last_month = dates[-1]
    train = all_rows[all_rows["target_date"] <= last_month]
    test = all_rows[all_rows["origin"] == last_month]
    pred = fit_predict(train, test)
    last = last_price(logp, last_month, test)
    future = test[[*KEYS, "target_date"]].rename(columns={"target_date": "date"}).assign(model="gbm")
    for col in QUANTILES:
        future[col] = np.exp(pred[col]).to_numpy() * last

    backtest = pd.concat(backtest_rows, ignore_index=True)
    metrics = pd.DataFrame(metric_rows)
    for df in (backtest, metrics, future):
        for col in ["product", "province_code"]:
            df[col] = df[col].astype(str)
    backtest = backtest[["date", *KEYS, "fold", "actual", "gbm", "lower_80", "upper_80"]].sort_values([*KEYS, "fold", "date"])
    future = future[["date", *KEYS, "model", "forecast", "lower_80", "upper_80"]].sort_values([*KEYS, "date"])

    backtest.round({"actual": 2, "gbm": 2, "lower_80": 2, "upper_80": 2}).to_csv(OUT / "gbm_backtest.csv", index=False, date_format="%Y-%m-%d")
    metrics.round(3).to_csv(OUT / "gbm_metrics.csv", index=False)
    future.round({c: 2 for c in QUANTILES}).to_csv(OUT / "gbm_forecasts.csv", index=False, date_format="%Y-%m-%d")
    if verbose:
        print(f"Wrote {future.groupby(KEYS).ngroups} series to models/gbm/")
    return backtest, metrics, future


if __name__ == "__main__":
    run()
