"""
News Article Analysis Tool
===========================
Thesis Version - Fixed & Improved
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


# ========================= CONFIGURATION =========================
DATA_FOLDER = Path(__file__).parent.parent / "Data"
# =================================================================


def main():
    print("News Article Analysis Tool (Thesis Version)\n")
    
    if not DATA_FOLDER.exists():
        print("❌ Data folder not found!")
        return
    
    csv_files = list(DATA_FOLDER.glob("*.csv"))
    print(f"Found {len(csv_files)} CSV files\n")
    
    all_dfs = []
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            all_dfs.append(df)
            print(f"✓ Loaded {len(df):5,} articles ← {file.name}")
        except Exception as e:
            print(f"✗ Failed {file.name}")
    
    if not all_dfs:
        return
    
    df = pd.concat(all_dfs, ignore_index=True)
    print(f"\n✅ Total Articles Loaded: {len(df):,}\n")
    
    # ====================== CLEANING ======================
    df.columns = df.columns.str.strip().str.lower()
    
    df = df.rename(columns={
        'website': 'source',
        'news_site': 'source',
        'publisher': 'source'
    })
    
    # Clean source column
    df['source'] = df['source'].astype(str).str.strip()
    df = df[df['source'] != 'nan']        # Remove NaN values
    
    # ====================== REPORT ======================
    now = datetime.now()
    print("=" * 95)
    print("NEWS ARTICLE ANALYSIS REPORT".center(95))
    print(f"Generated on: {now.strftime('%d %B %Y at %H:%M')}".center(95))
    print("=" * 95 + "\n")
    
    total = len(df)
    print(f"Total Articles Analyzed : {total:,}\n")
    
    # 1. Articles per Website
    print("1. ARTICLES PER NEWS WEBSITE")
    print("-" * 70)
    for source, count in df['source'].value_counts().items():
        print(f"{source:<40} : {count:6,}")
    print("-" * 70 + "\n")
    
    # 2. Overall Topic Breakdown
    if 'topic' in df.columns:
        print("2. BREAKDOWN BY TOPIC (Overall)")
        print("-" * 70)
        for topic, count in df['topic'].value_counts().items():
            pct = count / total * 100
            print(f"{topic:<40} : {count:6,} ({pct:5.1f}%)")
        print("-" * 70 + "\n")
    
    # 3. Topic Breakdown Per Website
    print("3. TOPIC BREAKDOWN PER WEBSITE")
    print("=" * 95)
    
    if 'topic' in df.columns and 'source' in df.columns:
        for website in sorted(df['source'].unique()):
            website_df = df[df['source'] == website]
            if len(website_df) == 0:
                continue
                
            print(f"\n{website.upper()} ({len(website_df)} articles):")
            
            topic_counts = website_df['topic'].value_counts()
            for topic, count in topic_counts.items():
                pct = count / len(website_df) * 100
                print(f"   • {topic:<38} : {count:5,} ({pct:5.1f}%)")
    
    print("\n" + "=" * 95)
    print("Analysis Completed Successfully!".center(95))
    print("=" * 95)


if __name__ == "__main__":
    main()