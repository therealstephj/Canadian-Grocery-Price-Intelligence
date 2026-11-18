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
- Two geographies are cities, not whole territories (Whitehorse, Yellowknife). See the week 1 decisions below.

## Week 1 decisions (agreed by the Project Lead, 2026-11-18)

These close the open questions above. Everyone builds against them.

### 1. Geography mapping

| Raw `GEO` | `province` | `province_code` |
|---|---|---|
| Canada | Canada | CA |
| Newfoundland and Labrador | Newfoundland and Labrador | NL |
| Prince Edward Island | Prince Edward Island | PE |
| Nova Scotia | Nova Scotia | NS |
| New Brunswick | New Brunswick | NB |
| Quebec | Quebec | QC |
| Ontario | Ontario | ON |
| Manitoba | Manitoba | MB |
| Saskatchewan | Saskatchewan | SK |
| Alberta | Alberta | AB |
| British Columbia | British Columbia | BC |
| Whitehorse, Yukon | Yukon | YT |
| Yellowknife, Northwest Territories | Northwest Territories | NT |

Territory values come from **one city each**, so label them that way on any chart or map (e.g. a footnote: "Yukon = Whitehorse, NWT = Yellowknife"). Nunavut is not in the price data.

### 2. CPI geographies
`cpi_clean.csv` keeps **only the 13 geographies above**, so prices and CPI join cleanly. The other 17 CPI geographies (16 cities and Iqaluit) are dropped in cleaning.

### 3. Product categories (`category` column)
Every product gets exactly one of these values (spelling matters, since Power BI slicers use them):

| category | examples |
|---|---|
| Meat and fish | beef cuts, pork cuts, chicken, bacon, wieners, salmon, shrimp |
| Dairy and eggs | milk, cream, butter, margarine, cheese, yogurt, eggs |
| Plant-based alternatives | soy milk, nut milk, tofu, meatless burgers |
| Fresh produce | fresh fruit and vegetables |
| Frozen foods | frozen vegetables, fries, pizza, strawberries |
| Bakery and grains | bread, flatbread, crackers, cookies, cereal, pasta, rice, flour |
| Pantry | sugar, oils, sauces, condiments, canned goods, nuts, peanut butter, hummus |
| Beverages | coffee, tea, juices |
| Baby | baby food, infant formula |
| Household and personal care | deodorant, shampoo, toothpaste, laundry detergent |

**Household and personal care** items stay in the clean data but are **not groceries**. Exclude them from grocery KPIs and charts (filter `category != 'Household and personal care'`).

### 4. Products sold in two sizes
Onions, oranges and potatoes appear both per kilogram and as a bag. Keep them as **separate products**. Do not merge them.

### 5. Forecast staples (business question 5)
The 8 items Forecasting & ML forecasts:

| Staple | Exact `product` value |
|---|---|
| Ground beef | Ground beef, per kilogram |
| Chicken breasts | Chicken breasts, per kilogram |
| Eggs | Eggs, 1 dozen |
| Milk | Milk, 4 litres |
| Butter | Butter, 454 grams |
| White bread | White bread, 675 grams |
| Coffee | Roasted or ground coffee, 340 grams |
| Bananas | Bananas, per kilogram |

All 8 have the full Jan 2017 history for Canada and every province, with one exception: **Milk, 4 litres is not reported for Newfoundland and Labrador** (StatCan publishes 1 L and 2 L milk there). Forecast milk for Canada and the other 9 provinces.
