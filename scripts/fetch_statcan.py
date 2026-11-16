"""Download the two StatCan tables and write small raw samples.

Usage (from the repo root):
    python scripts/fetch_statcan.py                  # download both tables, write samples
    python scripts/fetch_statcan.py --zip-dir ~/Downloads   # use zips you already downloaded

Outputs (in data/raw):
    18100245_prices_sample.csv   staple products only, 2019 onward
    18100004_cpi_sample.csv      all-items / food / food from stores / food from restaurants, 2019 onward

Standard library only. The full zips are saved to data/raw too but are git-ignored.
"""
import argparse
import csv
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

TABLES = {
    "18100245": "https://www150.statcan.gc.ca/n1/tbl/csv/18100245-eng.zip",
    "18100004": "https://www150.statcan.gc.ca/n1/tbl/csv/18100004-eng.zip",
}

# Edit these lists to change what goes into the sample.
STAPLE_KEYWORDS = ["beef", "egg", "bread", "coffee", "milk", "butter", "chicken"]
CPI_GROUPS = ["All-items", "Food", "Food purchased from stores", "Food purchased from restaurants"]
START_YEAR = 2019

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


def get_zip(table_id, zip_dir):
    """Return the zip bytes, from a local folder if given, otherwise from StatCan."""
    name = f"{table_id}-eng.zip"
    if zip_dir:
        path = Path(zip_dir).expanduser() / name
        if not path.exists():
            sys.exit(f"Could not find {path}. Download it from the table page or drop --zip-dir.")
        return path.read_bytes()
    print(f"Downloading {TABLES[table_id]} ...")
    with urllib.request.urlopen(TABLES[table_id], timeout=120) as resp:
        data = resp.read()
    (RAW / name).write_bytes(data)
    return data


def read_rows(zip_bytes, table_id):
    """Yield dict rows from the main data CSV inside the zip."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        member = f"{table_id}.csv"
        if member not in zf.namelist():
            member = next(n for n in zf.namelist() if n.endswith(".csv") and "MetaData" not in n)
        with zf.open(member) as fh:
            text = io.TextIOWrapper(fh, encoding="utf-8-sig", newline="")
            yield from csv.DictReader(text)


def product_column(fieldnames):
    """The product column is called 'Products' or 'Products and product groups'."""
    for name in fieldnames:
        if name.startswith("Products"):
            return name
    sys.exit(f"No 'Products' column found. Header was: {fieldnames}")


def write_sample(rows, out_path, keep):
    kept = 0
    writer = None
    with open(out_path, "w", newline="", encoding="utf-8") as out:
        for row in rows:
            if writer is None:
                writer = csv.DictWriter(out, fieldnames=list(row.keys()))
                writer.writeheader()
            if keep(row):
                writer.writerow(row)
                kept += 1
    print(f"Wrote {kept} rows to {out_path}")
    return kept


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--zip-dir", help="folder that already holds 18100245-eng.zip and 18100004-eng.zip")
    args = parser.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)

    for table_id, label, wanted in [
        ("18100245", "prices", lambda p: any(k in p.lower() for k in STAPLE_KEYWORDS)),
        ("18100004", "cpi", lambda p: p in CPI_GROUPS),
    ]:
        rows = read_rows(get_zip(table_id, args.zip_dir), table_id)
        first = next(rows)
        prod_col = product_column(list(first.keys()))

        def keep(row, prod_col=prod_col, wanted=wanted):
            year = int(row["REF_DATE"][:4])
            return year >= START_YEAR and wanted(row[prod_col])

        def with_first(first_row, rest):
            yield first_row
            yield from rest

        write_sample(with_first(first, rows), RAW / f"{table_id}_{label}_sample.csv", keep)

    print("Done. Check the sample files, then record the real column names in docs/data_dictionary.md.")


if __name__ == "__main__":
    main()
