# DAILYSTAR_NEWS_FINAL.PY
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import os
import pickle
import re
import ftfy
from tqdm import tqdm
import random
from zoneinfo import ZoneInfo
import signal
import sys

# ========================= CONFIG =========================
BASE_URL = "https://www.thedailystar.net/news/world"

import db

TABLE_NAME = "dailystar"
LAST_PAGE_PKL = os.path.join(db.DATA_DIR, "dailystar_last_page.pkl")

CUTOFF_DATE = datetime(2025, 6, 1)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}

TOPICS = {
    "Russia Ukraine war": ["russia", "ukraine", "putin", "zelensky", "kyiv", "kiev", "donbas", "crimea"],
    "Iran Israel war": ["iran", "israel", "tehran", "tel aviv", "houthis", "hezbollah", "hormuz", "iran war", "middle east war"],
    "Taiwan Strait conflict": ["taiwan strait", "taiwan invasion", "blockade taiwan", "invade taiwan",
                               "taiwan military", "china taiwan strait", "cross-strait"]
}

OPINION_KEYWORDS = ["opinion", "editorial", "analysis", "commentary", "op-ed", "column"]

# ====================== LOAD DATA ======================
articles_df = db.load_table(TABLE_NAME)
print(f"Loaded {len(articles_df)} existing articles from SQL.")

existing_urls = set(articles_df['url'].tolist())

start_page = 1
if os.path.exists(LAST_PAGE_PKL):
    with open(LAST_PAGE_PKL, "rb") as f:
        start_page = pickle.load(f) + 1
    print(f"Resuming from page {start_page}")

# ====================== DATE PARSER ======================
def parse_date(full_text: str) -> datetime | None:
    text_head = full_text[:4000]

    patterns = [
        r'UPDATED\s*(\d{1,2}\s+[A-Za-z]+\s+202[5-6](?:,\s*\d{1,2}:\d{2}\s*[AP]M)?)',
        r'(\d{1,2}\s+[A-Za-z]+\s+202[5-6],\s*\d{1,2}:\d{1,2}\s*[AP]M)',
        r'(\d{1,2}\s+[A-Za-z]+\s+202[5-6])'
    ]

    for pat in patterns:
        match = re.search(pat, text_head, re.IGNORECASE | re.DOTALL)
        if match:
            date_str = match.group(1) if match.group(1) else match.group(0)
            date_str = re.sub(r'^UPDATED\s*', '', date_str, flags=re.I).strip()
            date_str = re.sub(r',\s*\d{1,2}:\d{1,2}\s*[AP]M', '', date_str, flags=re.I).strip()

            for fmt in ["%d %B %Y", "%d %b %Y"]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.replace(hour=0, minute=0, second=0, microsecond=0)
                except ValueError:
                    continue
    return None

# ====================== FILTERS ======================
def is_opinion_piece(title: str, url: str) -> bool:
    title_lower = title.lower()
    url_lower = url.lower()
    if any(kw in title_lower for kw in OPINION_KEYWORDS):
        return True
    if any(kw in url_lower for kw in ['/opinion', '/editorial', '/analysis', '/column', '/view']):
        return True
    return False

def get_topic(title: str, text: str) -> str | None:
    combined = (title + " " + text[:2000]).lower()
    for topic_name, keywords in TOPICS.items():
        if any(kw in combined for kw in keywords):
            return topic_name
    return None

# ====================== ARTICLE PARSER ======================
def parse_article(url: str):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        title_tag = soup.find("h1") or soup.find("title")
        title = title_tag.get_text(strip=True).split("|")[0].strip() if title_tag else "No title"

        full_page = soup.get_text()
        published_date = parse_date(full_page)

        selectors = ["div.article-content", "div.entry-content", "article"]
        full_text = ""
        for sel in selectors:
            container = soup.select_one(sel)
            if container:
                ps = [p.get_text(strip=True) for p in container.find_all("p") if len(p.get_text(strip=True)) > 40]
                full_text = "\n\n".join(ps)
                break
        if not full_text:
            full_text = "\n\n".join([p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 40])

        full_text = ftfy.fix_text(full_text)
        full_text = re.sub(r'\s+', ' ', full_text).strip()
        title = ftfy.fix_text(title).strip()

        return title, published_date, full_text

    except Exception as e:
        print(f"   Error parsing {url}: {e}")
        return None, None, ""

# ====================== CTRL+C SAVE ======================
collected_articles = []
current_page = start_page

def signal_handler(sig, frame):
    print("\n\n⚠️ Interrupted! Saving progress...")
    if collected_articles:
        new_df = pd.DataFrame(collected_articles).drop_duplicates(subset=['url'])
        inserted = db.upsert_articles(TABLE_NAME, new_df)

        with open(LAST_PAGE_PKL, "wb") as f:
            pickle.dump(current_page - 1, f)

        print(f"✅ Saved {inserted} new articles. Resume from page {current_page} next time.")
    else:
        print("No new articles to save.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# ====================== MAIN ======================
def main():
    global current_page
    seen_this_run = set(existing_urls)
    stop_scraping = False

    bd_today = datetime.now(ZoneInfo("Asia/Dhaka")).strftime("%d-%m-%Y")
    print(f"Today in Bangladesh: {bd_today}")
    print("Starting faster scrape with proper date + topic grouping\n")

    while True:
        try:
            res = requests.get(f"{BASE_URL}?page={current_page}", headers=HEADERS, timeout=15)
            soup = BeautifulSoup(res.text, "html.parser")

            links = []
            for a in soup.select('h2 a[href], h3 a[href], .article-title a'):
                href = a.get('href')
                if not href: continue
                if href.startswith('/'):
                    href = "https://www.thedailystar.net" + href
                if "/news/world" not in href and "/news/" not in href: continue
                if any(x in href.lower() for x in ['/bangladesh', '/dhaka', '/metro', '/opinion']): continue
                if href in seen_this_run: continue

                links.append(href)
                seen_this_run.add(href)

            print(f"📄 Page {current_page}: {len(links)} new potential articles")

            if not links and current_page > 8:
                print("No more articles found.")
                break

        except Exception as e:
            print(f"Page {current_page} error: {e}")
            break

        for link_url in tqdm(links, desc=f"Page {current_page}", leave=False):
            if is_opinion_piece("", link_url): continue

            title, pub_date, full_text = parse_article(link_url)

            if pub_date is None or not full_text.strip(): continue
            if is_opinion_piece(title, link_url): continue
            if pub_date < CUTOFF_DATE:
                print("⏹️ Cutoff reached. Stopping...")
                stop_scraping = True
                break

            matched_topic = get_topic(title, full_text)
            if not matched_topic: continue

            collected_articles.append({
                "published_date": pub_date,
                "topic": matched_topic,
                "source": "The Daily Star",
                "region": "World",
                "title": title,
                "url": link_url,
                "full_text": full_text
            })

            print(f"   ✅ [{matched_topic}] {pub_date.strftime('%d-%m-%Y')} | {title[:70]}...")

            time.sleep(random.uniform(0.25, 0.45))

        if stop_scraping:
            break

        current_page += 1
        time.sleep(0.8)

    # ====================== FINAL SAVE ======================
    if collected_articles:
        new_df = pd.DataFrame(collected_articles).drop_duplicates(subset=['url'])
        inserted = db.upsert_articles(TABLE_NAME, new_df)
        total = len(db.load_table(TABLE_NAME))

        if os.path.exists(LAST_PAGE_PKL):
            os.remove(LAST_PAGE_PKL)

        print(f"\n✅ Done! Added {inserted} articles. Total in '{TABLE_NAME}' table: {total}")
    else:
        print("\nNo new articles with valid dates were found.")

if __name__ == "__main__":
    main()