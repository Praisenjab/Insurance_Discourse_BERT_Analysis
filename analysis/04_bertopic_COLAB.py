# ============================================================
# BERTopic ANALYSIS  (run in Google Colab)
#
# Produces the neural-embedding topic model to compare against
# the TF-IDF results. Outputs topic table, dimension breakdown,
# and interactive + static figures for Chapter 4.
#
# BEFORE RUNNING:
#   Runtime menu -> Change runtime type -> Hardware accelerator: T4 GPU
#   (Not essential, but makes embedding ~5x faster.)
#   Then upload corpus_final_v2.csv via the folder icon on the left.
# ============================================================

# ---- Cell 1: install ----
!pip install bertopic sentence-transformers -q

# ---- Cell 2: everything else ----
import re
import numpy as np
import pandas as pd
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP
from hdbscan import HDBSCAN

df = pd.read_csv("corpus_final_v2.csv")
df["text"] = df["text"].astype(str)
docs_df = df[df["word_count"] >= 8].reset_index(drop=True)
docs = docs_df["text"].tolist()
print(f"{len(df)} docs total, {len(docs)} with 8+ words sent to BERTopic")
print(docs_df["source"].value_counts().to_string(), "\n")

# Domain stopwords stripped at the topic-representation stage.
EXTRA = {
    "insurance","insurer","insurers","policy","policies","nigeria","nigerian",
    "just","like","get","got","also","would","could","one","na","dey","abeg",
    "please","thanks","thank","good","morning","hello","hi","sir","yes","ok",
    "okay","know","want","need","much","really","make","made","use","using",
    "app","apps","go","going","even","still","people","person","time","way",
}
vectorizer = CountVectorizer(stop_words=list(EXTRA), ngram_range=(1,2), min_df=3)

# Embeddings. all-MiniLM-L6-v2 is small, fast, and standard for short text.
embed_model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = embed_model.encode(docs, show_progress_bar=True)

# Fixed random_state so the run is reproducible (examiners like this).
umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0,
                  metric="cosine", random_state=42)
# min_cluster_size controls topic granularity; 15 suits a ~1000-doc corpus.
hdbscan_model = HDBSCAN(min_cluster_size=15, metric="euclidean",
                        cluster_selection_method="eom", prediction_data=True)

topic_model = BERTopic(
    embedding_model=embed_model,
    umap_model=umap_model,
    hdbscan_model=hdbscan_model,
    vectorizer_model=vectorizer,
    calculate_probabilities=True,
    verbose=True,
)

topics, probs = topic_model.fit_transform(docs, embeddings)
docs_df["topic"] = topics

info = topic_model.get_topic_info()
print("\n" + "="*80)
print("TOPICS FOUND (topic -1 = outliers/unclustered)")
print("="*80)
print(info[["Topic","Count","Name"]].to_string(index=False))

# ---- Map each topic to a literacy dimension by its keywords ----
DIMS = {
 "Terminology":["mean","meaning","term","comprehensive","third party","deductible","excess","pre existing","definition","difference"],
 "Coverage":["cover","covered","coverage","include","benefit","plan","hospital","treatment","limit","exclusion","drugs","accredited","school"],
 "Premium/Pricing":["price","cost","pay","amount","rate","expensive","cheap","annual","monthly","fee","worth","value","premium","payment"],
 "Claims process":["claim","claims","process","document","report","settle","payout","reject","denied","delay","refund","accident","approve","approval"],
 "Insurer trust/reliability":["scam","trust","reliable","legit","genuine","fraud","fake","best","recommend","experience","reputation"],
 "Consumer rights":["right","entitle","law","act","regulation","naicom","complaint","refuse","obligation","duty"],
 "Access/how-to":["register","registration","sign","enroll","portal","website","how","where","start","buy","code","receipt","office","login","password","email"],
}
def map_dim(topic_id):
    if topic_id == -1:
        return "Outlier"
    words = [w for w,_ in topic_model.get_topic(topic_id)]
    blob = " ".join(words)
    hits = {d: sum(1 for w in ws if w in blob) for d,ws in DIMS.items()}
    d = max(hits, key=hits.get)
    return d if hits[d] > 0 else "Unclassified"

info["dimension"] = info["Topic"].map(map_dim)
docs_df["dimension"] = docs_df["topic"].map(map_dim)

print("\n" + "="*60)
print("COMPREHENSION GAPS BY LITERACY DIMENSION (BERTopic)")
print("="*60)
excl_outliers = docs_df[docs_df["dimension"] != "Outlier"]
dim_counts = excl_outliers["dimension"].value_counts()
dim_pct = (100*dim_counts/dim_counts.sum()).round(1)
for d in dim_counts.index:
    print(f"  {d:30} {dim_counts[d]:4d} ({dim_pct[d]}%)")
outliers = (docs_df["topic"] == -1).sum()
print(f"\n  (outliers not classified: {outliers} docs = {round(100*outliers/len(docs_df),1)}%)")

# ---- Save outputs ----
info.to_csv("bertopic_topics.csv", index=False)
docs_df.to_csv("bertopic_docs.csv", index=False)
dim_counts.to_frame("count").to_csv("bertopic_dimensions.csv")

# ---- Figures ----
try:
    fig1 = topic_model.visualize_barchart(top_n_topics=12)
    fig1.write_html("bertopic_barchart.html")
    fig2 = topic_model.visualize_topics()
    fig2.write_html("bertopic_map.html")
    print("\nInteractive figures saved: bertopic_barchart.html, bertopic_map.html")
except Exception as e:
    print("viz skipped:", e)

import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(9,5))
dim_pct.sort_values().plot.barh(ax=ax, color="#6b46c1")
ax.set_xlabel("% of classified documents")
ax.set_title("Comprehension Gaps by Literacy Dimension (BERTopic, neural)")
plt.tight_layout(); plt.savefig("bertopic_dimensions.png", dpi=120)
print("Saved bertopic_dimensions.png")

from google.colab import files
for f in ["bertopic_topics.csv","bertopic_docs.csv","bertopic_dimensions.csv",
          "bertopic_dimensions.png","bertopic_barchart.html","bertopic_map.html"]:
    try: files.download(f)
    except Exception as e: print("download skip", f, e)
