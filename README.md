# News Bias Detector and Temporal Media Analysis System

A Python-based news scraping, dataset management, and media bias analysis system for comparing how Bangladeshi and international media report major geopolitical conflicts.

This project collects articles from multiple news outlets, stores them in structured datasets, and uses LLM-based analysis to compare narratives, framing, tone, emphasis, and bias across sources. It also includes temporal analysis to show how coverage changes over time.

## Overview

The project supports two major analysis modes:

1. Current Bias Comparison
   - Compares Bangladeshi media coverage with international media coverage for a selected topic and date range.

2. Temporal Change Analysis
   - Compares recent articles with older articles from selected time periods to identify how media framing, tone, language, and emphasis have changed.

The system is designed for academic research, thesis work, media monitoring, and comparative journalism studies.

## Key Features

- Scrapes articles from multiple news sources
- Stores clean article datasets in CSV and PKL formats
- Filters articles by topic, keyword, and date range
- Compares Bangladeshi vs international media narratives
- Detects framing, sourcing, selection, and linguistic bias
- Evaluates generated analysis quality using an academic-style evaluator
- Compares recent vs past coverage for temporal media analysis
- Provides a Streamlit-based user interface
- Handles mixed date formats across different news sources
- Supports daily article collection workflows

## News Sources

The system currently works with four news outlets.

### International Media

- BBC News
- The Guardian

### Bangladeshi Media

- The Daily Star
- New Age Bangladesh

These outlets were selected to compare international and Bangladeshi perspectives on major global events.

## Covered Topics

The project currently focuses on three geopolitical topics:

- Russia Ukraine war
- Iran Israel war
- Taiwan Strait conflict

Each article is filtered and grouped under one of these topics.

## What the System Does

The full pipeline works like this:

```text
News Websites
     |
     v
Scraper Scripts
     |
     v
Clean Article Extraction
     |
     v
CSV / PKL Dataset Storage
     |
     v
Search, Filtering, and Topic Selection
     |
     v
LLM-Based Bias and Temporal Analysis
     |
     v
Streamlit App Interface
```

## System Architecture

```text
+---------------------------+
|       News Sources        |
| BBC, Guardian, Daily Star |
| New Age Bangladesh        |
+-------------+-------------+
              |
              v
+---------------------------+
|      Scraper Layer        |
| requests, BeautifulSoup,  |
| Playwright, trafilatura   |
+-------------+-------------+
              |
              v
+---------------------------+
|       Data Layer          |
| CSV and PKL files stored  |
| inside the Data folder    |
+-------------+-------------+
              |
              v
+---------------------------+
|   Search and Filter Layer |
| date filtering, topic     |
| filtering, TF-IDF search  |
+-------------+-------------+
              |
              v
+---------------------------+
|      LLM Analysis Layer   |
| BiasEngine, BiasEvaluator |
| Temporal analysis module  |
+-------------+-------------+
              |
              v
+---------------------------+
|      Streamlit UI         |
| interactive analysis app  |
+---------------------------+
```

## Project Structure

```text
Bias-Detector/
|
├── Data/
│   ├── bbc.csv
│   ├── bbc.pkl
│   ├── guardian.csv
│   ├── guardian.pkl
│   ├── dailystar_news.csv
│   ├── newage_news.csv
│   └── newage_news.pkl
|
├── DAILY ARTICLES/
│   ├── BBCDAILY.py
│   ├── GUARDIANDAILY.py
│   ├── DAILYSTARDAILY.py
│   └── NEWAGEDAILY.py
|
├── SCRIPTS/
│   ├── app.py
│   ├── smart_system.py
│   ├── analysis.py
│   ├── llm.py
│   ├── BBC.PY
│   ├── GUARDIAN.PY
│   ├── Dailystar.py
│   ├── NEWAGE.PY
│   └── Articles.py
|
├── backup/
│   └── backup datasets and debug files
|
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Important Files

### SCRIPTS/app.py

The main Streamlit application.

It provides:

- Analysis mode selection
- Current bias comparison interface
- Temporal change analysis interface
- Result display
- Optional academic evaluation section

### SCRIPTS/smart_system.py

The main backend pipeline for loading, cleaning, searching, and analyzing article data.

It handles:

- Loading datasets from the Data folder
- Cleaning invalid rows
- Removing unusable article text
- Parsing mixed date formats
- Building a TF-IDF search index
- Searching by keyword, topic, and date
- Splitting articles into Bangladeshi and international media groups
- Compressing article text before LLM analysis
- Running the main bias comparison pipeline

### SCRIPTS/analysis.py

The temporal analysis module.

It handles:

- Recent vs past article comparison
- Per-newspaper temporal analysis
- Overall temporal change reporting
- International vs Bangladeshi temporal comparison
- Selection of recent and older article samples for each source

### SCRIPTS/llm.py

The OpenAI LLM integration module.

It contains:

- OpenAI client setup
- BiasEngine
- BiasEvaluator

BiasEngine generates the main media bias analysis.

BiasEvaluator evaluates the generated analysis against the original article texts.

### DAILY ARTICLES/

Contains daily scraper scripts for updating article datasets from each source.

### Data/

Contains the structured datasets used by the system.

## Analysis Modes

## 1. Current Bias Comparison

This mode compares Bangladeshi and international media coverage for a selected topic and date range.

Users can select:

- Keyword
- Topic
- Start date
- End date

The system then:

1. Loads all article datasets.
2. Filters articles by date, topic, and optional keyword.
3. Splits results into Bangladeshi and international media.
4. Compresses the selected article text.
5. Sends the text to the LLM.
6. Generates a structured media bias analysis.

The generated analysis includes:

- Bangladeshi narrative summary
- International narrative summary
- Framing comparison
- Bias detection
- Overall conclusion

Bias types considered include:

- Selection or omission bias
- Framing bias
- Linguistic bias
- Sourcing bias
- Nationalistic, ideological, or political bias

## 2. Academic Evaluation

After generating a current bias comparison, users can optionally run an evaluation.

The evaluation checks:

- Fidelity to the original texts
- Balance and fairness
- Evidence quality
- Framing analysis depth
- Bias detection accuracy
- Structure and clarity
- Overall objectivity

The evaluator provides scores and short justifications for each category.

## 3. Temporal Change Analysis

This mode compares recent coverage with older coverage for the same topic.

Users can select:

- Topic
- Comparison period

Available comparison periods:

- 7 days ago
- 1 month ago
- 3 months ago
- 6 months ago

The system compares:

- Recent articles from the last 10 days
- Past articles from the selected earlier period

For each newspaper, the system uses up to:

- 2 recent articles
- 2 past articles

The temporal analysis identifies:

- Changes in tone
- Changes in framing
- Changes in emphasis
- New angles introduced
- Angles that disappeared
- Changes in language intensity
- Differences between Bangladeshi and international coverage

The result includes:

- Overall temporal change report
- Per-newspaper analysis
- International vs Bangladeshi comparison

## Dataset Format

Each article row contains the following fields:

| Column | Description |
|---|---|
| published_date | Publication date of the article |
| topic | Assigned geopolitical topic |
| source | News outlet name |
| region | Region or section of the article |
| title | Article headline |
| url | Original article URL |
| full_text | Extracted article body text |

## Date Handling

Different news sources may store publication dates in different formats.

Examples:

- 2026-06-09
- 09-06-2026
- 09-06-26

The system includes custom date parsing logic to normalize these formats before filtering.

This is important because incorrect parsing can cause articles to appear in the wrong time period during temporal analysis.

## Technologies Used

The project uses:

- Python
- Streamlit
- pandas
- NumPy
- scikit-learn
- OpenAI API
- python-dotenv
- requests
- BeautifulSoup
- Playwright
- trafilatura
- fake-useragent
- tqdm
- ftfy
- python-dateutil
- lxml

## Installation

Clone the repository:

```bash
git clone https://github.com/RakibHasan221b/Bias-Detector.git
cd Bias-Detector
```

Create a virtual environment:

```bash
python -m venv thesis
```

Activate the environment.

On Windows:

```bash
thesis\Scripts\activate
```

On macOS or Linux:

```bash
source thesis/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install Playwright browsers:

```bash
playwright install
```

## Environment Variables

The LLM features require an OpenAI API key.

Create a `.env` file in the project root.

You can copy the example file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
copy .env.example .env
```

Add your API key:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

Do not commit your real `.env` file to GitHub.

## Running the App

From the project root, run:

```bash
streamlit run SCRIPTS/app.py
```

If you are already inside the `SCRIPTS/` folder, run:

```bash
streamlit run app.py
```

Streamlit will open the app in your browser.

## How to Use

### Current Bias Comparison

1. Open the Streamlit app.
2. Select `Current Bias Comparison (BD vs International)`.
3. Enter an optional keyword.
4. Select a topic.
5. Choose a start date and end date.
6. Click `Run Analysis`.
7. Read the generated bias analysis.
8. Optionally run the detailed academic evaluation.

### Temporal Change Analysis

1. Open the Streamlit app.
2. Select `Temporal Change Analysis (Recent vs Past)`.
3. Select a topic.
4. Select a past comparison period.
5. Click `Run Temporal Analysis`.
6. Read the overall report.
7. Expand each newspaper section to view source-specific changes.

## Scraping Workflow

The project includes source-specific scripts for collecting articles.

A typical scraping workflow is:

```text
Run scraper
     |
     v
Collect article links
     |
     v
Extract article title, date, URL, and body text
     |
     v
Classify article topic
     |
     v
Remove duplicates
     |
     v
Save updated CSV and PKL files
```

## Daily Update Workflow

The `DAILY ARTICLES/` folder contains scripts intended for daily updates.

A daily update process can work like this:

```text
Scheduled run
     |
     v
Run daily scraper scripts
     |
     v
Update files in Data/
     |
     v
Commit updated datasets
     |
     v
Push changes to GitHub
```

This can be automated using GitHub Actions or another scheduler.

## Example Outputs

The system can generate:

- Media narrative summaries
- Bangladeshi vs international framing comparison
- Bias detection reports
- Source-level temporal change analysis
- Overall temporal media trend reports
- Academic evaluation scores
- Evidence-based conclusions from selected articles

## Research Applications

This project can support research in:

- Media bias detection
- Political communication
- Framing theory
- Comparative journalism
- International communication
- Computational social science
- LLM-assisted qualitative analysis
- News narrative tracking

For academic use, LLM-generated outputs should be checked against the original articles and supported with direct textual evidence.

## Limitations

This project has some limitations:

- LLM-generated analysis may contain mistakes and should be manually verified.
- Analysis quality depends on the quality of scraped article text.
- News website structure changes may break scrapers.
- The system currently focuses on selected topics and selected sources.
- The OpenAI API is required for analysis features.
- API usage may involve cost.
- The system analyzes only the article text provided to it.

## Future Improvements

Possible future improvements include:

- Add more international and Bangladeshi news sources
- Add more geopolitical topics
- Add charts and visual dashboards
- Add downloadable PDF or DOCX reports
- Add article-level citation display
- Add sentiment analysis
- Add topic modeling
- Add named entity recognition
- Add source reliability metrics
- Add GitHub Actions automation for daily scraping
- Add database storage
- Add user-uploaded article comparison
- Add multilingual support

## Security Notes

- Keep your OpenAI API key private.
- Do not commit `.env` files.
- Review generated outputs before using them in formal research.
- Respect the terms of service of the news websites being scraped.

## Author

Rakib Hasan

GitHub: [RakibHasan221b](https://github.com/RakibHasan221b)

## Repository

GitHub Repository:

[https://github.com/RakibHasan221b/Bias-Detector](https://github.com/RakibHasan221b/Bias-Detector)

## Disclaimer

This project is for educational and research purposes. The analysis produced by the system should not be treated as absolute truth. LLM-generated outputs may contain errors, omissions, or misinterpretations. Any research conclusion should be checked against the original articles and supported by direct evidence.
