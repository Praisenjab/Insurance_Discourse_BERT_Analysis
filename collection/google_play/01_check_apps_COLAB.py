# ============================================================
# PASTE THIS WHOLE THING INTO ONE GOOGLE COLAB CELL AND RUN IT
# ============================================================

!pip install google-play-scraper pandas -q

import time
import pandas as pd
from google_play_scraper import search, app

BRANDS = [
    # Insurtech / digital-first
    "Casava insurance", "ETAP car insurance", "MyCoverGenius", "MyCover.ai",
    "Octamile", "PaddyCover", "Wella Health",
    # HMOs - expect the highest volume
    "RelianceHMO", "Reliance Health", "Hygeia HMO", "Avon HMO",
    "Clearline HMO", "Axa Mansard Health", "Leadway Health",
    # Traditional insurers
    "AXA Mansard", "Leadway Assurance", "AIICO Insurance",
    "Cornerstone Insurance", "Custodian Insurance", "NEM Insurance",
    "Mutual Benefits Assurance", "Sovereign Trust Insurance",
    "Prudential Zenith Life", "FBN Insurance", "Heirs Insurance",
    "Tangerine Life", "Old Mutual Nigeria",
    # Generic sweeps - catches anything missed above
    "insurance Nigeria", "health insurance Nigeria", "car insurance Nigeria",
]

seen, rows = {}, []

for brand in BRANDS:
    try:
        hits = search(brand, lang="en", country="ng", n_hits=4)
    except Exception as e:
        print(f"  search failed for {brand}: {e}")
        continue

    for h in hits:
        app_id = h.get("appId")
        if not app_id or app_id in seen:
            continue
        seen[app_id] = True
        try:
            d = app(app_id, lang="en", country="ng")
            rows.append({
                "search_term": brand,
                "app_id": app_id,
                "title": d.get("title"),
                "developer": d.get("developer"),
                "installs": d.get("installs"),
                "n_ratings": d.get("ratings"),
                "n_reviews": d.get("reviews"),
                "score": d.get("score"),
                "genre": d.get("genre"),
            })
            print(f"  {str(d.get('title'))[:38]:40} reviews={d.get('reviews')}")
        except Exception as e:
            print(f"  detail failed for {app_id}: {e}")
        time.sleep(0.4)

df = pd.DataFrame(rows)

if df.empty:
    print("\nNothing returned. Re-run the cell, or try again in a few minutes.")
else:
    df["n_reviews"] = pd.to_numeric(df["n_reviews"], errors="coerce").fillna(0).astype(int)
    df = df.sort_values("n_reviews", ascending=False)
    df.to_csv("app_candidates.csv", index=False)

    print("\n" + "=" * 70)
    print("TOP 25 BY REVIEW COUNT")
    print("=" * 70)
    print(df[["title", "app_id", "installs", "n_reviews", "score"]].head(25).to_string(index=False))
    print("\nTOTAL REVIEWS AVAILABLE:", df["n_reviews"].sum())
    print("Apps with 100+ reviews:", (df["n_reviews"] >= 100).sum())

    # download it to your laptop
    from google.colab import files
    files.download("app_candidates.csv")
