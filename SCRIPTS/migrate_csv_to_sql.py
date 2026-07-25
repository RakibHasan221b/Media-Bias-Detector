"""
One-time migration: load the legacy Data/*.csv files into the new
SQLite-backed article tables (Data/articles.db).

Run once when setting up SQL storage. Safe to re-run: duplicate urls
are skipped automatically by db.upsert_articles().
"""

import os

import pandas as pd

import db

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(REPO_ROOT, "Data")

# (csv filename) -> (table name, exact strftime format that CSV's published_date column uses)
# These formats were confirmed by inspecting the raw files, not guessed - pandas'
# automatic date inference is ambiguous for DD-MM vs MM-DD strings (e.g. "05-08-2025").
CSV_TO_TABLE = {
    "bbc.csv": ("bbc", "%Y-%m-%d"),
    "guardian.csv": ("guardian", "%Y-%m-%d"),
    "dailystar_news.csv": ("dailystar", "%d-%m-%y"),
    "newage_news.csv": ("newage", "%d-%m-%Y"),
}


def main():
    for csv_name, (table, date_format) in CSV_TO_TABLE.items():
        path = os.path.join(DATA_DIR, csv_name)

        if not os.path.exists(path):
            print(f"skip {csv_name}: file not found")
            continue

        df = pd.read_csv(path, low_memory=False, encoding="utf-8-sig")
        df["published_date"] = pd.to_datetime(df["published_date"], format=date_format, errors="coerce")
        before = len(db.load_table(table))
        inserted = db.upsert_articles(table, df)
        after = before + inserted

        print(f"{csv_name} -> {table}: {len(df)} rows in csv, {inserted} newly inserted, {after} total in table")

    print("\nMigration complete. Row counts per table:")
    for table in db.TABLES:
        print(f"  {table}: {len(db.load_table(table))}")


if __name__ == "__main__":
    main()
