# NEWAGE_NEWS_FINAL.PY
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
import sys

# ========================= CONFIG =========================
BASE_URL = "https://www.newagebd.net/articlelist/31/world"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(SCRIPT_DIR, "..", "SCRIPTS"))
import db

TABLE_NAME = "newage"
LAST_PAGE_PKL = os.path.join(db.DATA_DIR, "newage_last_page.pkl")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.newagebd.net/",
}

# ==================== TOPIC SCORING ====================
TOPICS = {
    "Russia Ukraine war": {
        "core": ["ukraine war", "russian invasion", "kyiv strike", "zelensky", "putin", "donbas", "crimea", "russian forces", "ukrainian army"],
        "support": ["russia", "ukraine", "kiev", "zelenskyy"]
    },
    "Iran Israel war": {
        "core": ["iran retaliates", "israel attacks", "israeli strike", "iranian missile", "tehran strikes", "netanyahu", "hezbollah", "houthis", "iran war", "israel war"],
        "support": ["iran", "israel", "tehran", "tel aviv", "middle east war", "gulf", "us israel"]
    },
    "Taiwan Strait conflict": {
        "core": ["taiwan strait", "pla navy", "taiwan incursion", "military drill", "chinese warship", "pla aircraft", "taiwan blockade", "cross strait tension", "beijing threatens taiwan"],
        "support": ["taiwan military", "taiwan independence", "taiwanese defense", "us taiwan", "taiwan arms"]
    }
}

OPINION_KEYWORDS = ["opinion", "editorial", "analysis", "commentary", "op-ed", "column"]

# ====================== LOAD DATA ======================
articles_df = db.load_table(TABLE_NAME)
print(f"Loaded {len(articles_df)} existing articles from SQL.")

existing_urls = set(articles_df['url'].tolist())

if not articles_df.empty:
    parsed_dates = pd.to_datetime(articles_df['published_date'], errors='coerce')
    latest_known_date = parsed_dates.max().date()
    print(f"Latest date in existing data: {latest_known_date.strftime('%d-%m-%Y')}")
else:
    latest_known_date = datetime(2025, 1, 1).date()

start_page = 1
if os.path.exists(LAST_PAGE_PKL):
    with open(LAST_PAGE_PKL, "rb") as f:
        start_page = pickle.load(f) + 1
    print(f"Resuming from page {start_page}")

# ====================== FILTERS ======================
def is_opinion_piece(title: str, url: str) -> bool:
    title_lower = (title or "").lower()
    url_lower = url.lower()
    if any(kw in title_lower for kw in OPINION_KEYWORDS):
        return True
    if any(kw in url_lower for kw in ['/opinion', '/editorial', '/analysis', '/column', '/view']):
        return True
    return False

def get_topic(title: str, text: str) -> str | None:
    if not title and not text:
        return None
    combined = (title + " " + text[:2500]).lower()
    best_topic = None
    best_score = 0
    for topic_name, data in TOPICS.items():
        core_hits = sum(2 for kw in data["core"] if kw in combined)
        support_hits = sum(1 for kw in data["support"] if kw in combined)
        total_score = core_hits + support_hits
        if total_score > best_score:
            best_score = total_score
            best_topic = topic_name
    return best_topic if best_score >= 3 else None

# ====================== ARTICLE PARSER ======================
def parse_article(url: str):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        title_tag = soup.find("h1") or soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else "No title"
        if "|" in title:
            title = title.split("|")[0].strip()

        published_date = None
        full_page = soup.get_text()
        matches = re.findall(r'(\d{1,2}\s+[A-Za-z]+\s*,\s*202[5-6](?:,\s*\d{1,2}:\d{2})?)', full_page)
        if matches:
            date_text = matches[0].strip()
            clean = re.sub(r'\s+', ' ', date_text).strip()
            formats = ["%d %B, %Y, %H:%M", "%d %B, %Y", "%d %B %Y, %H:%M", "%d %B %Y"]
            for fmt in formats:
                try:
                    dt = datetime.strptime(clean, fmt)
                    published_date = dt.date()
                    break
                except ValueError:
                    continue

        selectors = ["div.article-content", "div.post-content", "div.entry-content", "article", "div.content"]
        full_text = ""
        for sel in selectors:
            container = soup.select_one(sel)
            if container:
                paragraphs = container.find_all("p")
                cleaned_paras = [p.get_text(strip=True) for p in paragraphs 
                                if len(p.get_text(strip=True)) > 40 
                                and "Google News" not in p.get_text() 
                                and "Follow" not in p.get_text()]
                if cleaned_paras:
                    full_text = "\n\n".join(cleaned_paras)
                    break
        if not full_text:
            paragraphs = soup.find_all("p")
            cleaned_paras = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50]
            full_text = "\n\n".join(cleaned_paras)

        full_text = ftfy.fix_text(full_text)
        full_text = re.sub(r'[\u200b\u200c\u200d\u2060\xa0]', ' ', full_text)
        full_text = re.sub(r'\s+', ' ', full_text).strip()
        title = ftfy.fix_text(title)
        title = re.sub(r'\s+', ' ', title).strip()

        return title, published_date, full_text

    except Exception:
        return None, None, ""

# ====================== MAIN ======================
def main():
    current_page = start_page
    seen_this_run = set(existing_urls)
    consecutive_old_or_duplicate = 0
    max_consecutive = 15

    print(f"Today in Bangladesh: {datetime.now(ZoneInfo('Asia/Dhaka')).strftime('%d-%m-%Y')}")
    print("Starting New Age daily scraper...\n")

    while True:
        try:
            url = f"{BASE_URL}?page={current_page}" if current_page > 1 else BASE_URL
            res = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(res.text, "html.parser")

            links = []
            for a in soup.select('h2 a, h3 a, .news-title a, article a, a[href*="/post/"]'):
                href = a.get('href')
                if not href: continue
                if href.startswith('/'):
                    href = "https://www.newagebd.net" + href
                if "/post/" not in href or href in seen_this_run:
                    continue
                links.append(href)
                seen_this_run.add(href)

            print(f"📄 Page {current_page}: {len(links)} new potential articles")

            if not links and current_page > 25:        # safety limit
                print("No more articles found.")
                break

        except Exception as e:
            print(f"Page {current_page} error: {e}")
            break

        for link_url in tqdm(links, desc=f"Page {current_page}", leave=False):
            if is_opinion_piece("", link_url):
                continue

            title, pub_date, full_text = parse_article(link_url)

            if pub_date is None or not full_text.strip():
                continue

            if is_opinion_piece(title, link_url):
                continue

            # IMPROVED STOP LOGIC
            is_old = (pub_date < latest_known_date) if pub_date else True
            is_duplicate = (link_url in existing_urls)

            if is_duplicate or is_old:
                consecutive_old_or_duplicate += 1
                print(f"   🔁 Old/Duplicate: {pub_date.strftime('%d-%m-%Y') if pub_date else 'N/A'} | {title[:60]}...")
                if consecutive_old_or_duplicate >= max_consecutive:
                    print(f"⏹️ Stopping - {max_consecutive} consecutive old or duplicate articles reached.")
                    return collected_articles
            else:
                consecutive_old_or_duplicate = 0

            matched_topic = get_topic(title, full_text)
            if not matched_topic:
                continue

            collected_articles.append({
                "published_date": pub_date,
                "topic": matched_topic,
                "source": "New Age",
                "region": "World",
                "title": title,
                "url": link_url,
                "full_text": full_text
            })

            print(f"   ✅ [{matched_topic}] {pub_date.strftime('%d-%m-%Y')} | {title[:70]}...")

            time.sleep(random.uniform(0.3, 0.6))

        current_page += 1
        time.sleep(0.6)

    return collected_articles


# ====================== RUN ======================
if __name__ == "__main__":
    collected_articles = []
    collected = main()

    if collected:
        new_df = pd.DataFrame(collected).drop_duplicates(subset=['url'])
        inserted = db.upsert_articles(TABLE_NAME, new_df)
        total = len(db.load_table(TABLE_NAME))

        if os.path.exists(LAST_PAGE_PKL):
            os.remove(LAST_PAGE_PKL)

        print(f"\n✅ Done! Added {inserted} new articles. Total in '{TABLE_NAME}' table: {total}")
    else:
        print("\n✅ No new valid articles found today.")