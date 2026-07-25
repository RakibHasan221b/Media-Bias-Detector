"""
SQLite storage layer for the Bias Detector project.

Replaces the old per-source CSV + pickle files under Data/ with four tables
inside a single Data/articles.db file: bbc, guardian, dailystar, newage.
Every table has the same columns the CSVs had, so callers get the exact
same DataFrame shape back as before.
"""

import os
import sqlite3

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(REPO_ROOT, "Data")
DB_FILE = os.path.join(DATA_DIR, "articles.db")

TABLES = ["bbc", "guardian", "dailystar", "newage"]

COLUMNS = ["published_date", "topic", "source", "region", "title", "url", "full_text"]


def get_connection():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    init_db(conn)
    return conn


def init_db(conn):
    for table in TABLES:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                published_date TEXT,
                topic TEXT,
                source TEXT,
                region TEXT,
                title TEXT,
                url TEXT UNIQUE,
                full_text TEXT
            )
        """)
    conn.commit()


def _validate_table(name):
    if name not in TABLES:
        raise ValueError(f"Unknown table '{name}'. Expected one of {TABLES}")


def _normalize(df):
    """Make sure a DataFrame has exactly COLUMNS, in order, with published_date as
    a plain YYYY-MM-DD string. Handles ISO date strings (BBC/Guardian scrapers) as
    well as raw datetime.date/datetime.datetime objects (Dailystar/Newage scrapers)."""
    df = df.copy()
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[COLUMNS]

    df["published_date"] = pd.to_datetime(df["published_date"], errors="coerce").dt.strftime("%Y-%m-%d")

    return df


def load_table(name):
    """Read a whole table back into a DataFrame (same columns as the old CSVs).
    Returns an empty DataFrame with the right columns if the table has no rows yet."""
    _validate_table(name)

    conn = get_connection()
    try:
        df = pd.read_sql_query(f"SELECT {', '.join(COLUMNS)} FROM {name}", conn)
    finally:
        conn.close()
    return df


def upsert_articles(name, df):
    """Insert new articles into a table, skipping any row whose url already exists.
    Mirrors the old drop_duplicates(subset=['url']) + to_csv/to_pickle behaviour.
    Returns the number of rows actually inserted."""
    _validate_table(name)

    if df is None or len(df) == 0:
        return 0

    clean = _normalize(df)
    rows = [tuple(r) for r in clean.where(pd.notnull(clean), None).itertuples(index=False)]

    conn = get_connection()
    try:
        cursor = conn.executemany(
            f"INSERT OR IGNORE INTO {name} ({', '.join(COLUMNS)}) "
            f"VALUES ({', '.join(['?'] * len(COLUMNS))})",
            rows,
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()
