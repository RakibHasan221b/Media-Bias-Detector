"""
Fails the GitHub Action (red X + email) if an outlet has stopped collecting articles.
Runs as the last step of the daily workflow, after the data is committed.
"""
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Data", "articles.db")
MAX_DAYS_WITHOUT_NEWS = 4                      # allow quiet days, catch real breakages
ACTIVE_OUTLETS = ["bbc", "guardian", "dailystar"]  # newage paused (Cloudflare block)

con = sqlite3.connect(DB)
cutoff = (datetime.now(timezone.utc) - timedelta(days=MAX_DAYS_WITHOUT_NEWS)).strftime("%Y-%m-%d")
stale = []
for table in ACTIVE_OUTLETS:
    latest = con.execute(f"SELECT MAX(published_date) FROM {table}").fetchone()[0]
    print(f"{table:10s} latest article: {latest}")
    if not latest or str(latest)[:10] < cutoff:
        stale.append(f"{table} (latest {latest})")

if stale:
    sys.exit("No new articles for " + str(MAX_DAYS_WITHOUT_NEWS) + "+ days: " + ", ".join(stale))
print("All active outlets are up to date.")
