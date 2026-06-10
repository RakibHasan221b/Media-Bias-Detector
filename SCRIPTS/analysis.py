from datetime import datetime, timedelta

import pandas as pd

from llm import BiasEngine
from smart_system import SearchEngine, load_data


NEWSPAPERS = {
    "BBC": "International",
    "The Guardian": "International",
    "The Daily Star": "BD",
    "New Age": "BD",
}

PERIOD_DAYS = {
    "7 days ago": 7,
    "1 month ago": 30,
    "3 months ago": 90,
    "6 months ago": 180,
}


def _date_window(today, start_days_back, end_days_back):
    start = today - timedelta(days=start_days_back)
    end = today - timedelta(days=end_days_back)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def _source_articles(df, source):
    return df[df["source"].str.contains(source, case=False, na=False, regex=False)]


def _format_articles(texts):
    return "\n\n---\n\n".join(texts) if texts else "No articles found."


def _filter_articles(df, topic, start_date, end_date):
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)

    filtered = df.copy()
    filtered = filtered[filtered["published_date"] >= start]
    filtered = filtered[filtered["published_date"] <= end]
    filtered = filtered[filtered["topic"].str.contains(topic, case=False, na=False)]
    return filtered.sort_values("published_date", ascending=False)


def run_temporal_analysis(topic: str, time_period: str):
    if not topic or topic == "All":
        return "Please select a specific topic for temporal analysis.", {}, {}

    df = load_data()
    engine = SearchEngine(df)
    bias_engine = BiasEngine()

    today = datetime.now().date()
    days_back = PERIOD_DAYS.get(time_period, 30)

    recent_start, recent_end = _date_window(today, 10, 0)
    old_start, old_end = _date_window(today, days_back + 10, max(days_back - 5, 0))

    recent_df = _filter_articles(df, topic, recent_start, recent_end)
    old_df = _filter_articles(df, topic, old_start, old_end)

    recent_by_paper = {}
    old_by_paper = {}
    per_paper_analysis = {}

    for paper in NEWSPAPERS:
        recent_articles = _source_articles(recent_df, paper)
        old_articles = _source_articles(old_df, paper)

        recent_texts = engine.compress(recent_articles, max_articles=2)
        old_texts = engine.compress(old_articles, max_articles=2)

        recent_by_paper[paper] = recent_texts
        old_by_paper[paper] = old_texts

        if not recent_texts and not old_texts:
            per_paper_analysis[paper] = "No matching articles found for either comparison window."
            continue

        prompt = f"""You are a media trends analyst.

Newspaper: {paper}
Topic: {topic}
Comparison: recent coverage vs {time_period}

Recent period ({recent_start} to {recent_end}):
{_format_articles(recent_texts)}

Past period ({old_start} to {old_end}):
{_format_articles(old_texts)}

Provide a short, evidence-based analysis of what changed:
1. Shifts in tone, framing, or emphasis
2. New angles introduced or dropped
3. Changes in language intensity
4. What became more or less prominent

Use only the supplied article text. If evidence is limited, say so."""

        try:
            response = bias_engine.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a precise media change analyst."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=850,
                temperature=0.3,
            )
            per_paper_analysis[paper] = response.choices[0].message.content
        except Exception as e:
            per_paper_analysis[paper] = f"Analysis error: {str(e)}"

    all_recent = [text for texts in recent_by_paper.values() for text in texts]
    all_old = [text for texts in old_by_paper.values() for text in texts]

    bd_recent = [
        text
        for paper, texts in recent_by_paper.items()
        if NEWSPAPERS[paper] == "BD"
        for text in texts
    ]
    bd_old = [
        text
        for paper, texts in old_by_paper.items()
        if NEWSPAPERS[paper] == "BD"
        for text in texts
    ]
    intl_recent = [
        text
        for paper, texts in recent_by_paper.items()
        if NEWSPAPERS[paper] == "International"
        for text in texts
    ]
    intl_old = [
        text
        for paper, texts in old_by_paper.items()
        if NEWSPAPERS[paper] == "International"
        for text in texts
    ]

    global_prompt = f"""You are an expert media trends analyst.

Topic: {topic}
Comparison: recent coverage vs {time_period}
Recent period: {recent_start} to {recent_end}
Past period: {old_start} to {old_end}

Recent articles across all outlets:
{_format_articles(all_recent[:8])}

Past articles across all outlets:
{_format_articles(all_old[:8])}

Bangladeshi media recent:
{_format_articles(bd_recent[:4])}

Bangladeshi media past:
{_format_articles(bd_old[:4])}

International media recent:
{_format_articles(intl_recent[:4])}

International media past:
{_format_articles(intl_old[:4])}

Write a concise report on how coverage changed across BBC, The Guardian, The Daily Star, and New Age.
Include a short section comparing international vs Bangladeshi media changes.
Use only the supplied article text and note when evidence is limited."""

    try:
        global_resp = bias_engine.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a precise, evidence-based media trends analyst."},
                {"role": "user", "content": global_prompt},
            ],
            max_tokens=1300,
            temperature=0.25,
        )
        global_analysis = global_resp.choices[0].message.content
    except Exception as e:
        global_analysis = f"Global analysis error: {str(e)}"

    metadata = {
        "period": time_period,
        "recent_start": recent_start,
        "recent_end": recent_end,
        "old_start": old_start,
        "old_end": old_end,
        "recent_count": len(recent_df),
        "past_count": len(old_df),
    }

    return global_analysis, per_paper_analysis, metadata