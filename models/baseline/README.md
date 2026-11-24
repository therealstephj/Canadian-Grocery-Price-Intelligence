# Seasonal-naive baseline (board card #20)

This is the benchmark for business question 5. Every later forecasting model (#21, #22) is scored against it, so a model is only worth using if it beats these numbers.

## Method

The forecast for a month is the price in the same month one year earlier: `forecast(t) = price(t - 12)`.

- **Series:** the 8 agreed staples (`docs/shared_schema.md`, decision 5) for Canada and each geography that has enough data.
- **Holdout:** the last 12 months of data (Oct 2025 to Sep 2026). Each holdout forecast uses only data from before the holdout.
- **Future forecast:** the next 12 months (Oct 2026 to Sep 2027), which repeats the last 12 observed months.
- **Metrics:** MAE and RMSE in dollars, plus MAPE (%) so products with different prices can be compared.

## Run it

```bash
python models/baseline/seasonal_naive.py
```

It needs pandas and numpy. It reads `data/clean/prices_clean.csv` once that file exists. Until then it reads the raw StatCan file and maps it to the shared schema names.

## Outputs

| File | Contents |
|---|---|
| `baseline_forecasts.csv` | `date, province, province_code, product, split, model, actual, forecast`. `split` is `backtest` (holdout months, with actuals) or `future` (no actuals yet). |
| `baseline_metrics.csv` | One row per series: `mae, rmse, mape_pct, mean_actual` on the 12-month holdout. |

## Results: Canada, 12-month holdout

| Staple | MAE ($) | RMSE ($) | MAPE (%) | Mean price ($) |
|---|---:|---:|---:|---:|
| Eggs, 1 dozen | 0.08 | 0.10 | 1.8 | 4.81 |
| Butter, 454 grams | 0.09 | 0.15 | 1.6 | 5.75 |
| Milk, 4 litres | 0.21 | 0.21 | 3.0 | 6.93 |
| White bread, 675 grams | 0.12 | 0.13 | 3.3 | 3.59 |
| Chicken breasts, per kilogram | 0.90 | 1.11 | 6.1 | 14.58 |
| Bananas, per kilogram | 0.15 | 0.17 | 7.8 | 1.81 |
| Ground beef, per kilogram | 1.93 | 1.97 | 12.0 | 16.08 |
| Roasted or ground coffee, 340 grams | 1.42 | 1.71 | 15.2 | 9.39 |

The baseline is already close for stable dairy and bread prices. It misses most on **coffee and ground beef**, because their prices rose steadily over the year and a same-month-last-year forecast can't follow a trend. Those are the series where #21 and #22 have the most room to improve.

## Limits

- **No trend:** a seasonal-naive forecast assumes this year looks like last year. For prices that are still rising, it forecasts too low.
- **One holdout window:** these metrics come from a single 12-month split. A rolling-origin backtest would give steadier numbers and is planned for #21.
- **Territories excluded:** Whitehorse (Yukon) and Yellowknife (NWT) prices only start in Sep 2025, so they don't yet have the 24 months needed. Milk 4 L is not reported for Newfoundland and Labrador. In total, 87 series are forecast (10 geographies × 8 staples, plus 7 for NL).
