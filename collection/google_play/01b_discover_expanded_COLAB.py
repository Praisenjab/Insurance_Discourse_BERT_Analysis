# ============================================================
# STEP 1b - EXPANDED DISCOVERY (replaces the first script)
# Covers NAICOM insurers, NHIA HMOs, takaful, insurtechs, NHIA.
# Paste into a Google Colab cell. Runs ~8-12 minutes.
# ============================================================

!pip install google-play-scraper pandas -q

import time
import pandas as pd
from google_play_scraper import search, app

BRANDS = [
    # ---- HMOs (highest expected review volume) ----
    "Hygeia HMO", "Reliance Health HMO", "Avon HMO", "Avon Healthcare",
    "Total Health Trust", "THT Nigeria health", "Redcare HMO",
    "Novo Health Africa", "AIICO Multishield", "Integrated Healthcare Nigeria",
    "Greenbay HMO", "Anchor HMO", "Princeton Health Nigeria",
    "United Healthcare International Nigeria", "Prepaid Medicare",
    "Songhai Health Trust", "Ultimate Health HMO", "Wellness HMO Nigeria",
    "Venus Medicare", "Police Health Maintenance", "Defence Health Maintenance",
    "Bastion Health", "Marina Medical HMO", "Salus Trust", "Sterling Health HMO",
    "Zenith Medicare", "Roding Healthcare", "Mediplan Healthcare",
    "Oceanic Health Management", "Clearline HMO", "Hallmark HMO",
    "Leadway Health", "NEM Health", "AXA Mansard Health", "Wella Health Nigeria",

    # ---- NAICOM-licensed insurers ----
    "AXA Mansard", "Leadway Assurance", "AIICO Insurance",
    "Custodian Insurance Nigeria", "Cornerstone Insurance",
    "Consolidated Hallmark Insurance", "Coronation Insurance", "Wapic Insurance",
    "NEM Insurance", "Mutual Benefits Assurance", "Sovereign Trust Insurance",
    "Lasaco Assurance", "Linkage Assurance", "Regency Alliance Insurance",
    "Guinea Insurance", "Prestige Assurance", "Universal Insurance Nigeria",
    "Anchor Insurance Nigeria", "Veritas Kapital Assurance", "Staco Insurance",
    "Sterling Assurance Nigeria", "SUNU Assurances Nigeria", "Unitrust Insurance",
    "Royal Exchange Insurance", "International Energy Insurance", "KBL Insurance",
    "Fin Insurance Nigeria", "Enterprise Life Nigeria", "African Alliance Insurance",
    "Capital Express Assurance", "Great Nigeria Insurance",
    "Standard Alliance Insurance", "NSIA Insurance Nigeria",
    "Zenith General Insurance", "Zenith Life Assurance",
    "Nigerian Agricultural Insurance", "Old Mutual Nigeria",
    "Tangerine Life", "Tangerine General Insurance", "Heirs Life Assurance",
    "Heirs General Insurance", "FBN Insurance", "Sanlam Nigeria",
    "SanlamAllianz Nigeria", "Allianz Nigeria", "Prudential Zenith Life",
    "Law Union and Rock",

    # ---- Takaful ----
    "Jaiz Takaful", "Noor Takaful", "Salam Takaful Nigeria", "Cornerstone Takaful",

    # ---- Insurtech ----
    "Casava insurance", "ETAP insure", "MyCoverGenius", "MyCover ai insurance",
    "Octamile", "PaddyCover", "Curacel", "Bluewave insurance",
    "Turaco insurance", "Gari motor insurance", "Hobbiton insurance",

    # ---- Scheme / regulator ----
    "NHIA Nigeria", "MyNHIA", "National Health Insurance Authority",

    # ---- Generic sweeps ----
    "health insurance Nigeria", "car insurance Nigeria", "motor insurance Nigeria",
    "life insurance Nigeria", "HMO Nigeria", "insurance claim Nigeria",
    "medical insurance Nigeria", "travel insurance Nigeria",
    "third party insurance Nigeria", "buy insurance Nigeria",
]

# Used only to FLAG likely-relevant rows. You still eyeball the output.
NG_KEYWORDS = [
    "hygeia", "reliance", "avon", "total health", "redcare", "novo health",
    "aiico", "integrated health", "greenbay", "anchor", "princeton",
    "prepaid medicare", "songhai", "ultimate health", "venus", "bastion",
    "marina", "salus", "roding", "mediplan", "oceanic", "clearline",
    "hallmark", "leadway", "nem ", "nemhmo", "axa mansard", "mansard",
    "wella", "custodian", "cornerstone insurance", "coronation", "wapic",
    "mutual benefits", "sovereign trust", "lasaco", "linkage", "regency",
    "guinea insurance", "prestige assurance", "universal insurance",
    "veritas", "staco", "sunu", "unitrust", "royal exchange", "kbl",
    "enterprise life", "african alliance", "capital express",
    "great nigeria", "standard alliance", "nsia", "zenith general",
    "zenith life", "naic", "old mutual general", "tangerine", "heirs",
    "fbn insurance", "sanlam", "allianz", "prudential zenith", "jaiz",
    "noor takaful", "salam takaful", "casava", "etap", "mycovergenius",
    "mycover.ai", "octamile", "paddycover", "curacel", "bluewave",
    "turaco", "hobbiton", "nhia", "national health insurance",
]

# Obvious noise seen in the first run.
EXCLUDE = [
    "notion", "monzo", "grab", "finch", "icici", "bajaj", "walaa", "hayah",
    "marshmallow", "learnzapp", "kids360", "sekiapp", "feraset", "octaverum",
    "melody", "song", "music", "opay", "okash", "carbon", "piggy", "autochek",
    "subsplash", "apollos", "used cars", "car mart", "automile", "mirae",
    "oraimo", "trustbanc", "cyberspace", "casa bank", "sofri", "investnaija",
    "cousant", "shibly", "icarslist", "kineapps", "ship afrika", "chuuma",
    "maytronics", "golyv", "rumbl", "aiconomy", "cornerstone ondemand",
    "cornerstone community", "reliance foundation", "reliancefs", "egypt",
    "ghana", "kenya", "zambia", "cyprus", "tbc insurance", "nemi mobility",
]

def flagged(title, dev, genre):
    blob = f"{title} {dev}".lower()
    if any(x in blob for x in EXCLUDE):
        return False
    return any(k in blob for k in NG_KEYWORDS)

seen, rows = set(), []

for i, brand in enumerate(BRANDS, 1):
    print(f"[{i}/{len(BRANDS)}] {brand}")
    try:
        hits = search(brand, lang="en", country="ng", n_hits=4)
    except Exception as e:
        print(f"    search failed: {e}")
        continue

    for h in hits:
        app_id = h.get("appId")
        if not app_id or app_id in seen:
            continue
        seen.add(app_id)
        try:
            d = app(app_id, lang="en", country="ng")
            title, dev = str(d.get("title")), str(d.get("developer"))
            rows.append({
                "search_term": brand,
                "app_id": app_id,
                "title": title,
                "developer": dev,
                "installs": d.get("installs"),
                "n_ratings": d.get("ratings"),
                "n_reviews": d.get("reviews"),
                "score": d.get("score"),
                "genre": d.get("genre"),
                "keep": flagged(title, dev, d.get("genre")),
            })
        except Exception as e:
            print(f"    detail failed {app_id}: {e}")
        time.sleep(0.35)

df = pd.DataFrame(rows)

if df.empty:
    print("\nNothing returned. Re-run the cell.")
else:
    df["n_reviews"] = pd.to_numeric(df["n_reviews"], errors="coerce").fillna(0).astype(int)
    df = df.sort_values(["keep", "n_reviews"], ascending=[False, False])
    df.to_csv("app_candidates_v2.csv", index=False)

    keep = df[df["keep"]]
    print("\n" + "=" * 78)
    print("FLAGGED AS NIGERIAN INSURANCE / HMO")
    print("=" * 78)
    print(keep[["title", "app_id", "developer", "installs", "n_reviews", "score"]]
          .to_string(index=False))
    print(f"\nApps flagged: {len(keep)}")
    print(f"Total reviews available: {keep['n_reviews'].sum()}")
    print(f"Apps with 50+ reviews: {(keep['n_reviews'] >= 50).sum()}")
    print(f"Apps with 10+ reviews: {(keep['n_reviews'] >= 10).sum()}")
    print(f"\nUnflagged rows also saved (keep=False) - scan them for anything I missed.")

    from google.colab import files
    files.download("app_candidates_v2.csv")
