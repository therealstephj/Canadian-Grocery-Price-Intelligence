#!/usr/bin/env bash
# Turn docs/board_cards.csv into GitHub issues (one per card).
# Run from the repo root after `gh auth login`.
# Then open your GitHub Project board and use "Add item" to bulk-add the issues.
set -euo pipefail

python3 - <<'PY'
import csv, subprocess

with open("docs/board_cards.csv", newline="", encoding="utf-8") as fh:
    for row in csv.DictReader(fh):
        body = (
            f"**Role:** {row['role']}\n"
            f"**Suggested owner:** {row['suggested_owner']}\n"
            f"**Week:** {row['week']}\n"
            f"**Deliverable:** `{row['deliverable']}`\n\n"
            f"{row['description']}\n"
        )
        subprocess.run(
            ["gh", "issue", "create", "--title", row["title"], "--body", body],
            check=True,
        )
        print("created:", row["title"])
PY
