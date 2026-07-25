import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

import db
from llm import BiasEngine


def parse_news_dates(series):
    """Parse the mixed date formats used by the scraped CSV files."""
    raw = series.astype(str).str.strip()

    parsed = pd.to_datetime(raw, format="%Y-%m-%d", errors="coerce")

    remaining = parsed.isna()
    if remaining.any():
        parsed.loc[remaining] = pd.to_datetime(
            raw.loc[remaining],
            format="%d-%m-%Y",
            errors="coerce",
        )

    remaining = parsed.isna()
    if remaining.any():
        parsed.loc[remaining] = pd.to_datetime(
            raw.loc[remaining],
            format="%d-%m-%y",
            errors="coerce",
        )

    remaining = parsed.isna()
    if remaining.any():
        parsed.loc[remaining] = pd.to_datetime(raw.loc[remaining], errors="coerce")

    return parsed


def load_data():
    dfs = []

    for name in db.TABLES:
        try:
            df = db.load_table(name)
            df["media_type"] = "BD" if name in ["dailystar", "newage"] else "International"
            print(f"Loaded {name}: {len(df)} rows")
            dfs.append(df)

        except Exception as e:
            print(f"Error loading {name}: {e}")
            continue

    if not dfs:
        raise FileNotFoundError("No data found in Data/articles.db. Check if the database exists and has rows.")

    df = pd.concat(dfs, ignore_index=True)

    df["published_date"] = parse_news_dates(df["published_date"])

    before = len(df)
    df = df[df["full_text"].notna()]
    df = df[df["full_text"].str.strip().str.len() > 30]
    df = df[df["published_date"].notna()]
    after = len(df)

    print("\n=== FINAL DATA SUMMARY ===")
    print(f"Rows before cleaning: {before} | After: {after}")
    print(f"BD rows: {len(df[df['media_type'] == 'BD'])}")
    print(f"International rows: {len(df[df['media_type'] == 'International'])}")

    return df


class SearchEngine:
    def __init__(self, df):
        self.df = df.copy().reset_index(drop=True)
        self.df["search_text"] = (
            self.df["title"].fillna("") + " " + self.df["full_text"].fillna("")
        )

        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=15000,
            min_df=1,
            lowercase=True,
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df["search_text"])

        print(f"TF-IDF vocabulary size: {len(self.vectorizer.vocabulary_)}")

    def _balanced_results(self, data, limit):
        """Return equal BD and International articles whenever both sides exist."""
        if len(data) == 0 or "media_type" not in data.columns:
            return data.head(limit)

        bd = data[data["media_type"] == "BD"]
        intl = data[data["media_type"] == "International"]

        if len(bd) == 0 or len(intl) == 0:
            return data.head(limit)

        per_side_limit = min(len(bd), len(intl), max(limit // 2, 1))

        balanced = pd.concat([bd.head(per_side_limit), intl.head(per_side_limit)])

        sort_columns = []
        ascending = []
        if "score" in balanced.columns:
            sort_columns.append("score")
            ascending.append(False)
        if "published_date" in balanced.columns:
            sort_columns.append("published_date")
            ascending.append(False)

        if sort_columns:
            balanced = balanced.sort_values(sort_columns, ascending=ascending)

        return balanced.head(limit)

    def search(self, keyword=None, topic=None, start_date=None, end_date=None):
        data = self.df.copy()

        if start_date:
            start_date = pd.to_datetime(start_date)
            data = data[data["published_date"] >= start_date]

        if end_date:
            end_date = pd.to_datetime(end_date)
            data = data[data["published_date"] <= end_date]

        if topic and topic != "All":
            data = data[data["topic"].str.contains(topic, case=False, na=False)]

        if keyword and str(keyword).strip():
            query_vec = self.vectorizer.transform([keyword])
            scores = (self.tfidf_matrix @ query_vec.T).toarray().flatten()

            scored_df = self.df.copy()
            scored_df["score"] = scores

            if start_date:
                scored_df = scored_df[scored_df["published_date"] >= start_date]

            if end_date:
                scored_df = scored_df[scored_df["published_date"] <= end_date]

            if topic and topic != "All":
                scored_df = scored_df[
                    scored_df["topic"].str.contains(topic, case=False, na=False)
                ]

            terms = [t.strip() for t in str(keyword).lower().split() if t.strip()]
            if terms:
                pattern = "|".join(terms)
                mask = scored_df["search_text"].str.lower().str.contains(
                    pattern,
                    na=False,
                    regex=True,
                )
                scored_df.loc[mask, "score"] += 2.0

            scored_df = scored_df.sort_values("score", ascending=False)
            data = self._balanced_results(scored_df, 60)
        else:
            data = data.sort_values("published_date", ascending=False)
            data = self._balanced_results(data, 80)

        return data

    def split_media(self, df):
        return df[df["media_type"] == "BD"], df[df["media_type"] == "International"]

    def compress(self, df, max_articles=10):
        if len(df) == 0:
            return []

        texts = []

        for _, row in df[["title", "full_text"]].head(max_articles).iterrows():
            text = str(row["full_text"])[:3000]
            texts.append(f"TITLE: {row['title']}\n\nTEXT: {text}")

        return texts


def run_analysis(keyword=None, topic=None, start_date=None, end_date=None):
    df = load_data()
    engine = SearchEngine(df)
    llm = BiasEngine()

    filtered = engine.search(
        keyword=keyword,
        topic=topic,
        start_date=start_date,
        end_date=end_date,
    )

    print(
        f"DEBUG: Total articles found = {len(filtered)} | "
        f"BD: {len(filtered[filtered['media_type'] == 'BD'])} | "
        f"International: {len(filtered[filtered['media_type'] == 'International'])}"
    )

    if len(filtered) == 0:
        return "No relevant articles found. Try different dates or keywords.", [], []

    bd_df, intl_df = engine.split_media(filtered)
    bd_texts = engine.compress(bd_df)
    intl_texts = engine.compress(intl_df)

    clean_topic = topic if topic and topic != "All" else (keyword or "General News")

    result = llm.analyze(
        bd_texts=bd_texts,
        intl_texts=intl_texts,
        topic=clean_topic,
        start_date=start_date or "N/A",
        end_date=end_date or "N/A",
    )

    return result, bd_texts, intl_texts