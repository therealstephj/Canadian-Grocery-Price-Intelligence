# Business questions and KPIs

Everything we build should help answer one of these. If a task does not, question it.

| # | Question | KPI(s) | Data | Main owner |
|---|---|---|---|---|
| 1 | Which grocery items have risen most since 2019, and which ones in the last 12 months? | % change vs 2019 baseline; year-over-year % change; top 10 risers | Retail prices (18-10-0245-01) | EDA, SQL |
| 2 | Has food inflation outpaced overall inflation, and has it slowed down? | Food CPI vs all-items CPI, year-over-year % change; gap in percentage points | CPI (18-10-0004-01) | EDA, SQL |
| 3 | Which provinces were hit hardest? | Province food CPI % change vs 2019; province rank | CPI by province | SQL, Power BI |
| 4 | Has the price of groceries risen faster than the price of eating out? | Food from stores CPI vs food from restaurants CPI, indexed to 2019 = 100 | CPI | SQL, Power BI |
| 5 | Where are staple prices likely heading next year? | 6 to 12 month forecast for 5 to 8 staples; MAE and RMSE vs seasonal-naive baseline | Retail prices | ML |

## Definitions

- **Baseline**: 2019 average (pre-pandemic). Change vs 2019 = (current price / 2019 average price - 1) x 100.
- **Year-over-year %**: (price this month / price same month last year - 1) x 100.
- **Staples**: start with beef, eggs, bread, coffee. Final list agreed in week 1.

## Out of scope

- Store-level or brand-level prices (the data is national and provincial averages).
- Causes of inflation (we describe what happened, we do not prove why).
