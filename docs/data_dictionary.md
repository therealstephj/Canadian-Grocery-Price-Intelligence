# Data dictionary and source log

Owner: Project Lead. Fill this in as you go, not at the end.

## Source log

| Table | Title | Publisher | URL | Date downloaded | Downloaded by | Licence |
|---|---|---|---|---|---|---|
| 18-10-0245-01 | Monthly average retail prices for selected products | Statistics Canada | https://doi.org/10.25318/1810024501-eng | TBD | TBD | Open Government Licence - Canada |
| 18-10-0004-01 | Consumer Price Index, monthly, not seasonally adjusted | Statistics Canada | https://doi.org/10.25318/1810000401-eng | TBD | TBD | Open Government Licence - Canada |

## Raw columns

Fill in from the real downloaded header (first run of `scripts/fetch_statcan.py`).

| column | meaning | notes |
|---|---|---|
| TBD | | |

## Known limitations

Add to this as the team finds things. Starting list to verify against the data:

- [ ] Products are added or dropped over time, so some series have gaps.
- [ ] Prices are averages across stores, not specific stores or brands.
- [ ] Not every province has every product.
- [ ] CPI is an index, not a dollar price; do not compare the two directly without indexing both to 2019.
- [ ] Unit of measure can differ between products (per kg, per dozen, per litre).
