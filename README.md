# Canadian Grocery Price Intelligence

A five-person data analytics portfolio project. We use Statistics Canada data to answer one question: what happened to grocery prices in Canada, where did it hit hardest, and where are staple prices heading next?

## Business questions

1. Which grocery items have risen most since 2019, and which ones in the last 12 months?
2. Has food inflation outpaced overall inflation, and has it slowed down?
3. Which provinces were hit hardest?
4. Has the price of groceries risen faster than the price of eating out?
5. Where are staple prices likely heading next year?

Full detail and the KPI behind each question: [docs/business_questions.md](docs/business_questions.md)

## Data

Both tables are from Statistics Canada (Open Government Licence - Canada):

- Monthly average retail prices for selected products, table 18-10-0245-01
- Consumer Price Index, monthly, table 18-10-0004-01 (all-items, food, food from stores, food from restaurants, by province)

See [docs/data_dictionary.md](docs/data_dictionary.md) for columns, source log and known limitations.

## Team and roles

| Role | Stage | Owner |
|---|---|---|
| Project Lead and Data Sourcing | 1 | Stephanie |
| Data Cleaning and EDA | 2 | Haritha |
| SQL and Data Modelling | 3 | Jay |
| Power BI Dashboard | 4a | Danny |
| Forecasting and ML | 4b | Samir |

## Repo structure

```
data/raw        untouched downloads from StatCan (never edit these by hand)
data/clean      cleaned CSVs from the EDA role
notebooks/      EDA and forecasting notebooks
sql/            schema, reusable queries, KPI views
dashboard/      Power BI file, screenshots, dashboard guide
models/         forecasting code and saved results
docs/           business questions, data dictionary, schema, board cards
scripts/        helper scripts (data fetch, issue creation)
```

## Getting started

```bash
git clone https://github.com/therealstephj/Canadian-Grocery-Price-Intelligence.git
cd Canadian-Grocery-Price-Intelligence
python scripts/fetch_statcan.py
```

How we work (branches, pull requests, reviews): [CONTRIBUTING.md](CONTRIBUTING.md)

## Results

Filled in at the end of week 6: recommendations, dashboard screenshots, forecast results.
