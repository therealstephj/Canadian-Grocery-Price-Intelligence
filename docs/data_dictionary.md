# Data dictionary and source log

Owner: Project Lead. Keep this updated as the team finds things.

## Source log

| Table | Title | Publisher | URL | Date downloaded | Downloaded by | Licence |
|---|---|---|---|---|---|---|
| 18-10-0245-01 | Monthly average retail prices for selected products | Statistics Canada | https://doi.org/10.25318/1810024501-eng | 2026-11-16 | Stephanie | Open Government Licence - Canada |
| 18-10-0004-01 | Consumer Price Index, monthly, not seasonally adjusted | Statistics Canada | https://doi.org/10.25318/1810000401-eng | 2026-11-16 | Stephanie | Open Government Licence - Canada |

The raw files in `data/raw` are made by `scripts/fetch_statcan.py`: **every product in the price table**, and the four CPI groups below, from **January 2017** (the first month of the price table) onward. 2019 stays the comparison baseline. Re-run the script to refresh them. Never edit them by hand.

| Raw file | Rows | Months | What it holds |
|---|---|---|---|
| `data/raw/18100245_prices.csv` | 142,740 | 2017-01 → 2026-09 | All 110 products, 13 geographies |
| `data/raw/18100004_cpi.csv` | 8,142 | 2017-01 → 2026-10 | All-items, Food, Food purchased from stores, Food purchased from restaurants; 30 geographies |

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
| STATUS | StatCan data-quality flag | `..` = value not available (37 price rows, VALUE is blank). Blank everywhere else |
| SYMBOL | StatCan footnote symbol | Always blank in both files |
| TERMINATED | Flag for series that ended | Always blank: no product series has ended |
| DECIMALS | Decimal places StatCan reports | 2 for prices, 1 for CPI |

### Mapping to the shared schema

| Raw | Clean (see `docs/shared_schema.md`) |
|---|---|
| REF_DATE | `date` (first of month) |
| GEO | `province`, `province_code` |
| Products (prices) | `product` and `unit` (split the text) |
| Products and product groups (CPI) | `cpi_group` |
| VALUE (prices) | `price` |
| VALUE (CPI) | `cpi_value` |

## Products in the price table

110 products. The full list is in the raw file (`Products` column); the groups below are a starting point for the EDA role's `category` column.

- **Meat and fish:** beef (4 cuts + ground), pork (3 cuts), chicken (whole, breasts, thighs, drumsticks), bacon, wieners, salmon, shrimp, canned salmon and tuna
- **Dairy and eggs:** milk (1, 2, 4 L), cream, butter, margarine, block cheese, yogurt, eggs; plant-based soy milk, nut milk, tofu, meatless burgers
- **Fresh produce:** about 25 fruits and vegetables (apples, bananas, avocados, lettuce, potatoes, tomatoes…)
- **Frozen:** vegetables, fries, pizza, strawberries
- **Bakery, grains and pantry:** bread, flatbread, crackers, cookies, cereal, pasta, rice, flour, sugar, oils, sauces and condiments, canned goods, nuts, coffee, tea, juices
- **Baby:** baby food, infant formula
- **Not food (4):** deodorant, shampoo, toothpaste, laundry detergent. Decide in cleaning whether to drop them or keep them in a separate category; they are not groceries in the CPI "food" sense.

### Product-name gotchas (for cleaning)
- **Trailing spaces** in some names, e.g. `"Brown rice, 900 grams "`. Strip whitespace before anything else.
- **Unit is inside the name** after the last comma (`per kilogram`, `500 grams`, `unit`, `1 dozen`). One exception: `Tea (20 bags)` has no comma.
- **Same item in two sizes:** onions, oranges and potatoes appear both per kilogram and as a bag (1.36 kg / 4.54 kg). Keep them as separate products.

## Geography

| | Price table (13) | CPI table (30) |
|---|---|---|
| Canada | ✓ | ✓ |
| 10 provinces | ✓ | ✓ |
| Whitehorse, Yukon / Yellowknife, NWT | ✓ (cities) | ✓ |
| Iqaluit, Nunavut | ✗ | ✓ |
| Other cities (Toronto, Vancouver, Montréal…) | ✗ | ✓ (16 cities) |

**Coverage:** every province has all 110 products (Newfoundland and Labrador has 109). Whitehorse has only 59 and Yellowknife only 40, so territory comparisons only work for the products they share.
**Join rule:** the price geographies are a subset of the CPI geographies with identical names, so they join on `GEO` directly. For province-level comparisons, keep only Canada + the 10 provinces (+ the two territory cities if needed) on the CPI side.

## Known limitations

Confirmed in the data:

- [x] The unit of measure is inside the product name in the price table, and units differ (per kilogram, per litre, per dozen, grams), so products are not directly comparable by dollar value.
- [x] Two territory entries are cities, not whole territories (Whitehorse, Yellowknife), so "province" is not strictly accurate for them. Rule needed in cleaning.
- [x] CPI is an index (2002=100), not a dollar price. Index both series to 2019 before comparing them.
- [x] Not every geography has every product: the two territory cities are partial (59 and 40 products).
- [x] 37 price values are missing (`STATUS = ..`), all in Whitehorse (7) and Yellowknife (30), mostly flatbread, orange juice and white bread.
- [x] CPI covers 30 geographies including 16 cities and Iqaluit; prices cover 13. Names match exactly where they overlap.
- [x] No product series starts late or ends early between Jan 2017 and Sep 2026, and nothing is flagged TERMINATED.
- [x] The price table includes 4 non-food items (deodorant, shampoo, toothpaste, laundry detergent).

Still to verify:

- [ ] Prices are averages across stores, not specific stores or brands (check StatCan's methodology note).
- [ ] Outliers and sudden jumps in individual series (EDA role).
