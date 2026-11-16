# Data dictionary and source log

Owner: Project Lead. Keep this updated as the team finds things.

## Source log

| Table | Title | Publisher | URL | Date downloaded | Downloaded by | Licence |
|---|---|---|---|---|---|---|
| 18-10-0245-01 | Monthly average retail prices for selected products | Statistics Canada | https://doi.org/10.25318/1810024501-eng | 2026-11-16 | Stephanie | Open Government Licence - Canada |
| 18-10-0004-01 | Consumer Price Index, monthly, not seasonally adjusted | Statistics Canada | https://doi.org/10.25318/1810000401-eng | 2026-11-16 | Stephanie | Open Government Licence - Canada |

Samples in `data/raw` were made by `scripts/fetch_statcan.py` (2019 onward only; prices limited to staple keywords, CPI limited to four groups). Re-run the script to refresh them. Never edit them by hand.

| Sample file | Rows | What it holds |
|---|---|---|
| `data/raw/18100245_prices_sample.csv` | 21,611 | 21 products (see below) |
| `data/raw/18100004_cpi_sample.csv` | 6,486 | All-items, Food, Food purchased from stores, Food purchased from restaurants |

## Raw columns

Both tables share the same 15 columns. Only the product column name differs: `Products` in the price table, `Products and product groups` in the CPI table.

| column | meaning | notes |
|---|---|---|
| REF_DATE | Reference month, `YYYY-MM` | Add `-01` to make a real date |
| GEO | Geography | See "Geography" below |
| DGUID | StatCan geographic identifier | Different vintage per table (`2021A...` prices, `2016A...` CPI); not needed for analysis |
| Products / Products and product groups | The item or CPI group | In the price table the unit is part of this text, e.g. "Eggs, 1 dozen" |
| UOM | Unit of measure | Prices: `Dollars`. CPI: `2002=100` (index, base year 2002) |
| UOM_ID | Numeric code for UOM | Not needed |
| SCALAR_FACTOR | Scale of VALUE | `units` in the rows seen |
| SCALAR_ID | Numeric code for scale | Not needed |
| VECTOR | StatCan series ID, e.g. `v1353834271` | Handy for tracing a series back to StatCan |
| COORDINATE | Position of the series in the table | Not needed |
| VALUE | The number | Price in dollars, or CPI index value |
| STATUS | StatCan data-quality flag | Blank in the rows seen; check for non-blank values during EDA |
| SYMBOL | StatCan footnote symbol | Blank in the rows seen; check during EDA |
| TERMINATED | Flag for series that ended | Blank in the rows seen; check during EDA |
| DECIMALS | Decimal places StatCan reports | 2 for prices, 1 for CPI in the rows seen |

### Mapping to the shared schema

| Raw | Clean (see `docs/shared_schema.md`) |
|---|---|
| REF_DATE | `date` (first of month) |
| GEO | `province`, `province_code` |
| Products (prices) | `product` and `unit` (split the text) |
| Products and product groups (CPI) | `cpi_group` |
| VALUE (prices) | `price` |
| VALUE (CPI) | `cpi_value` |

## Products in the price sample

Beef: stewing cuts, striploin cuts, top sirloin cuts, rib cuts, ground beef (per kilogram).
Chicken: whole chicken, breasts, thigh, drumsticks (per kilogram).
Dairy and eggs: milk 1 litre / 2 litres / 4 litres, soy milk 1.89 litres, nut milk 1.89 litres, butter 454 grams, eggs 1 dozen.
Bakery and pantry: white bread 675 grams, flatbread and pita 500 grams, crackers and crisp breads 200 grams, roasted or ground coffee 340 grams, peanut butter 1 kilogram.

Soy milk, nut milk, flatbread, crackers and peanut butter came in only because the fetch script matches on keywords ("milk", "bread", "butter"). Keep or drop them during cleaning.

## Geography (price sample)

Canada, the ten provinces, plus two cities: Whitehorse (Yukon) and Yellowknife (Northwest Territories). Nunavut and Iqaluit do not appear in the price sample. The CPI geographies have not been checked yet.

## Known limitations

Confirmed in the data:

- [x] The unit of measure is inside the product name in the price table, and units differ (per kilogram, per litre, per dozen, grams), so products are not directly comparable by dollar value.
- [x] Two territory entries are cities, not whole territories (Whitehorse, Yellowknife), so "province" is not strictly accurate for them. Rule needed in cleaning.
- [x] CPI is an index (2002=100), not a dollar price. Index both series to 2019 before comparing them.

Still to verify:

- [ ] Products are added or dropped over time, so some series have gaps.
- [ ] Prices are averages across stores, not specific stores or brands.
- [ ] Not every province has every product.
- [ ] Non-blank STATUS, SYMBOL or TERMINATED values.
- [ ] CPI geographies and whether they match the price geographies.
