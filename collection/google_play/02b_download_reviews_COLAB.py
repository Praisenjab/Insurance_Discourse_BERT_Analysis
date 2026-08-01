# ============================================================
# STEP 2 - DOWNLOAD REVIEW TEXT
# Reads researcher reviewed app IDs from app_candidates_v3.csv.
#
# Before running: upload app_candidates_v3.csv using the folder
# icon in Colab's left sidebar.
# ============================================================

!pip install google-play-scraper pandas -q

import time
import pandas as pd
from google_play_scraper import reviews, Sort

MIN_REVIEWS = 1         # skip apps with fewer than this
CSV = "app_candidates_v3.csv"

cand = pd.read_csv(CSV)
cand["n_reviews"] = pd.to_numeric(cand["n_reviews"], errors="coerce").fillna(0).astype(int)

# Only the flagged Nigerian insurance apps with some volume.
targets = cand[(cand["keep"] == True) & (cand["n_reviews"] >= MIN_REVIEWS)]
targets = targets.drop_duplicates(subset=["app_id"]).sort_values("n_reviews", ascending=False)

print(f"Downloading from {len(targets)} apps "
      f"({targets['n_reviews'].sum()} reviews reported available)\n")

all_rows = []

for _, row in targets.iterrows():
    app_id, label = row["app_id"], row["title"]
    print(f"--- {label} ({app_id}) ---")
    collected, token, guard = [], None, 0
    try:
        while guard < 60:                      # hard stop, avoids infinite loops
            batch, token = reviews(
                app_id, lang="en", country="ng",
                sort=Sort.NEWEST, count=200, continuation_token=token,
            )
            if not batch:
                break
            collected.extend(batch)
            guard += 1
            if token is None:
                break
            time.sleep(1.0)
    except Exception as e:
        print(f"    stopped early: {e}")

    for r in collected:
        all_rows.append({
            "source": "play_store",
            "app_id": app_id,
            "app_name": label,
            "developer": row["developer"],
            "review_id": r.get("reviewId"),
            "text": r.get("content"),
            "rating": r.get("score"),
            "thumbs_up": r.get("thumbsUpCount"),
            "date": r.get("at"),
            "reply": r.get("replyContent"),
        })
    print(f"    got {len(collected)}")

df = pd.DataFrame(all_rows)

if df.empty:
    print("\nNothing downloaded. Check that 'keep' column has True values.")
else:
    df = df.dropna(subset=["text"])
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"].str.len() > 0].drop_duplicates(subset=["review_id"])
    df["word_count"] = df["text"].str.split().str.len()

    print("\n" + "=" * 60)
    print("TOTAL REVIEWS DOWNLOADED:", len(df))
    print("Median words:", int(df["word_count"].median()))
    print("Reviews with 10+ words:", (df["word_count"] >= 10).sum())
    print("Reviews with 20+ words:", (df["word_count"] >= 20).sum())
    print("=" * 60)
    print(df.groupby("app_name").size().sort_values(ascending=False).to_string())

    df.to_csv("play_reviews_raw.csv", index=False)
    from google.colab import files
    files.download("play_reviews_raw.csv")
