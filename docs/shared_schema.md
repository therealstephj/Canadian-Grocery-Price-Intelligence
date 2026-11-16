# Shared schema (agreed column names)

This is the contract between roles. SQL, Power BI and ML all build against these names from day one, before cleaning is finished. Change only with team agreement.

## Clean price table: `data/clean/prices_clean.csv`

| column | type | example | notes |
|---|---|---|---|
| date | date | 2024-03-01 | first day of the reference month |
| province | text | Ontario | full province name |
| province_code | text | ON | two-letter code; `CA` for Canada |
| product | text | Eggs, 1 dozen | standardized product name |
| category | text | Dairy and eggs | grouping used for slicers (assigned by EDA role) |
| unit | text | dozen | standardized unit |
| price | numeric | 4.12 | dollars per unit |

## Clean CPI table: `data/clean/cpi_clean.csv`

| column | type | example | notes |
|---|---|---|---|
| date | date | 2024-03-01 | first day of the reference month |
| province | text | Ontario | full province name |
| province_code | text | ON | `CA` for Canada |
| cpi_group | text | Food purchased from stores | all-items, food, food from stores, food from restaurants |
| cpi_value | numeric | 162.4 | index value (base year per StatCan table notes) |

## Star schema (SQL role)

- `fact_price(date_key, geography_key, product_key, price)`
- `dim_date(date_key, date, year, month, quarter)`
- `dim_geography(geography_key, province, province_code)`
- `dim_product(product_key, product, category, unit)`

CPI gets its own fact table (`fact_cpi`) sharing the same date and geography dimensions.

## Notes

- Raw StatCan column names are mapped to the names above by the EDA role. The mapping table is in `docs/data_dictionary.md`.
- In the raw price table the unit is part of the product text (for example "Eggs, 1 dozen"). The EDA role splits it into `product` and `unit`.
- CPI values are on a 2002=100 base. Indexing to 2019=100 for comparisons is done in cleaning/SQL, not in the raw data.
- Two geographies are cities, not whole territories (Whitehorse, Yellowknife). Agree on how they map to `province` and `province_code` in week 1 and write the rule here.
