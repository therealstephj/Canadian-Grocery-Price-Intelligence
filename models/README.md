# Forecasting and ML

Business question 5: **where are staple prices likely heading next year?** The models forecast the 8 agreed staples 12 months ahead for Canada and the 10 provinces, 87 series in all. The territories are left out because their prices only start in Sep 2025, and so is milk 4 L in NL, which isn't reported there.

| Folder / file | What it is | Board card |
|---|---|---|
| `baseline/` | Seasonal naive: the price in the same month last year | #20 |
| `sarima/` | SARIMA on log price, orders chosen by AIC | #21 |
| `gbm/` | Gradient boosting with lag features, one model for all series | #22 |
| `results.csv` | **The table for the dashboard**, built from all three | #23 |
| `build_results.py` | Rebuilds `results.csv` from the three models' outputs | #23 |

The full comparison, with charts and limits, is in [`notebooks/forecasting.ipynb`](../notebooks/forecasting.ipynb).

## Rebuild everything

```bash
pip install -r requirements.txt
python models/baseline/seasonal_naive.py   # seconds
python models/sarima/sarima.py             # about 5 minutes
python models/gbm/gbm.py                   # about 40 seconds
python models/build_results.py             # seconds
```

## `results.csv`: guide for the dashboard

One row per **model × series × future month**: 3 models × 87 series × 12 months = 3,132 rows. The forecast runs from Oct 2026 to Sep 2027, starting from the latest data (Sep 2026).

`date`, `province`, `province_code` and `product` use the same names and values as `fact_price` (`docs/shared_schema.md`), so forecasts join to `dim_date`, `dim_geography` and `dim_product` exactly like actual prices.

| Column | Type | Example | Meaning |
|---|---|---|---|
| `date` | date | 2027-03-01 | Forecast month (first day of the month) |
| `province` | text | Ontario | Full name; `Canada` for the national series |
| `province_code` | text | ON | Two-letter code; `CA` for Canada |
| `product` | text | Eggs, 1 dozen | Exact product name from the shared schema |
| `model` | text | gbm | `gbm`, `sarima` or `seasonal_naive` |
| `model_label` | text | Gradient boosting | Display name for slicers and legends |
| `is_headline` | 0/1 | 1 | **1 = the forecast to show by default** (gradient boosting) |
| `horizon_months` | int | 6 | Months after the latest data (1 to 12) |
| `forecast` | numeric | 5.02 | Forecast price in dollars |
| `lower_80`, `upper_80` | numeric | 4.85, 5.16 | 80% interval. Empty for `seasonal_naive` |
| `latest_date` | date | 2026-09-01 | Last month of actual data |
| `latest_price` | numeric | 4.83 | Actual price in `latest_date` |
| `change_vs_latest_pct` | numeric | 3.9 | `(forecast / latest_price - 1) × 100` |
| `backtest_mae`, `backtest_rmse` | numeric | 0.21 | Average error in dollars over three past test years |
| `backtest_mape_pct` | numeric | 4.43 | Average error as a % of price over the same test years |

### Suggested visuals

- **KPI cards:** filter `is_headline = 1` and `horizon_months = 12` to show "expected price in Sep 2027" and `change_vs_latest_pct` for each staple.
- **Line chart:** actual `price` from `fact_price`, followed by `forecast` from this table, with `lower_80` and `upper_80` as a shaded band. Put `model_label` on a slicer so readers can switch models, defaulting to gradient boosting.
- **Trust indicator:** show `backtest_mape_pct` next to each forecast, for example "typically within 4% in past years".
- **Footnote:** "Forecasts are statistical estimates from past prices only. They don't account for tariffs, weather or supply shocks. 80% intervals were slightly too narrow in testing."

### Headline forecast, Canada, Sep 2027 (gradient boosting)

| Staple | Sep 2026 | Sep 2027 forecast | Change | 80% interval | Past error (MAPE) |
|---|---:|---:|---:|---|---:|
| Ground beef, per kilogram | $16.92 | $18.35 | +8.5% | $16.56 to $20.10 | 5.0% |
| Roasted or ground coffee, 340 grams | $9.27 | $9.66 | +4.2% | $9.33 to $10.41 | 6.2% |
| Eggs, 1 dozen | $4.83 | $5.02 | +3.9% | $4.85 to $5.16 | 4.4% |
| Milk, 4 litres | $6.99 | $7.21 | +3.1% | $7.03 to $7.62 | 0.8% |
| Chicken breasts, per kilogram | $14.48 | $14.86 | +2.6% | $14.10 to $16.27 | 8.2% |
| White bread, 675 grams | $3.58 | $3.67 | +2.5% | $3.54 to $3.93 | 3.1% |
| Butter, 454 grams | $5.58 | $5.67 | +1.6% | $5.41 to $6.36 | 4.9% |
| Bananas, per kilogram | $1.88 | $1.89 | +0.5% | $1.84 to $2.02 | 3.5% |

### For the SQL role

The star schema doesn't have a forecast table yet. A suggested shape that reuses the existing dimensions:

```sql
fact_forecast(date_key, geography_key, product_key, model, model_label, is_headline,
              horizon_months, forecast, lower_80, upper_80, latest_price,
              change_vs_latest_pct, backtest_mae, backtest_rmse, backtest_mape_pct)
```

The dates run to Sep 2027, so `dim_date` needs to cover those months.
