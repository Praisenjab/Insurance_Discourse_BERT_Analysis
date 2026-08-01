from __future__ import annotations

import hashlib
import json
import platform
from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics import adjusted_rand_score, silhouette_score


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source" / "seminar files"
OUT = ROOT / "revised_analysis"
SOURCE_TFIDF_FIGURE = SOURCE / "fig_dimensions_v2.png"
ORIGINAL_TFIDF_FIGURE = (
    SOURCE_TFIDF_FIGURE
    if SOURCE_TFIDF_FIGURE.exists()
    else ROOT / "fig_dimensions_v2.png"
)
OUT.mkdir(parents=True, exist_ok=True)


TOPIC_AUDIT = {
    -1: {
        "audited_category": "Outlier",
        "audit_confidence": "Not applicable",
        "audit_rationale": (
            "The retained BERTopic output assigned these documents to the model outlier "
            "class. No manual category was imposed."
        ),
    },
    0: {
        "audited_category": "Trust and reliability",
        "audit_confidence": "High",
        "audit_rationale": (
            "Representative and sampled documents compare HMOs, providers, service "
            "credibility, and reliability."
        ),
    },
    1: {
        "audited_category": "Procedural access",
        "audit_confidence": "High",
        "audit_rationale": (
            "Documents mainly ask where and how to register, locate an office, and "
            "complete enrolment."
        ),
    },
    2: {
        "audited_category": "Procedural access",
        "audit_confidence": "High",
        "audit_rationale": (
            "Documents mainly concern login, password, account, and application access "
            "procedures."
        ),
    },
    3: {
        "audited_category": "Coverage and entitlements",
        "audit_confidence": "Moderate",
        "audit_rationale": (
            "Most inspected documents concern NHIS benefits, covered services, "
            "eligibility, entitlements, and scheme rules. This corrects the paper's "
            "unsupported Access label and the code's Unclassified label."
        ),
    },
    4: {
        "audited_category": "Residual or mixed",
        "audit_confidence": "High",
        "audit_rationale": (
            "The cluster is dominated by reactions, thanks, interpersonal exchanges, "
            "and unrelated or low information content."
        ),
    },
    5: {
        "audited_category": "Procedural access",
        "audit_confidence": "Moderate",
        "audit_rationale": (
            "Documents focus on failed payments, missing payment history, and steps "
            "needed to restore or use service. They do not consistently express a "
            "pricing knowledge gap."
        ),
    },
    6: {
        "audited_category": "Procedural access",
        "audit_confidence": "High",
        "audit_rationale": (
            "Documents mainly concern registration follow up, activation, and "
            "enrolment procedures."
        ),
    },
    7: {
        "audited_category": "Residual or mixed",
        "audit_confidence": "Moderate",
        "audit_rationale": (
            "Documents mix promotional HMO content, general praise, access concerns, "
            "and trust comments without one defensible dominant knowledge gap."
        ),
    },
    8: {
        "audited_category": "Procedural access",
        "audit_confidence": "High",
        "audit_rationale": (
            "Documents mainly ask how to change, select, or use a hospital or provider."
        ),
    },
    9: {
        "audited_category": "Residual or mixed",
        "audit_confidence": "High",
        "audit_rationale": (
            "The cluster contains promotional, devotional, generic, and unrelated "
            "material. It cannot support a terminology finding."
        ),
    },
    10: {
        "audited_category": "Procedural access",
        "audit_confidence": "Moderate",
        "audit_rationale": (
            "Documents mainly concern using application benefits, telemedicine, and "
            "service functionality, with some coverage content."
        ),
    },
}


CATEGORY_ORDER = [
    "Procedural access",
    "Trust and reliability",
    "Coverage and entitlements",
    "Residual or mixed",
    "Outlier",
]


CATEGORY_COLORS = {
    "Procedural access": "#1F4E79",
    "Trust and reliability": "#4F81BD",
    "Coverage and entitlements": "#70AD47",
    "Residual or mixed": "#A5A5A5",
    "Outlier": "#D9D9D9",
}


EXTRA_STOP_WORDS = {
    "insurance",
    "insurer",
    "insurers",
    "policy",
    "policies",
    "nigeria",
    "nigerian",
    "naira",
    "nairaland",
    "youtube",
    "app",
    "apps",
    "company",
    "companies",
    "service",
    "services",
    "people",
    "person",
    "thing",
    "things",
    "know",
    "think",
    "want",
    "need",
    "good",
    "like",
    "just",
    "really",
    "please",
    "thanks",
    "thank",
    "yes",
    "no",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def percent_table(
    data: pd.DataFrame,
    group_column: str | None = None,
    category_column: str = "audited_category",
) -> pd.DataFrame:
    if group_column is None:
        counts = (
            data[category_column]
            .value_counts()
            .reindex(CATEGORY_ORDER, fill_value=0)
            .rename_axis("category")
            .reset_index(name="document_count")
        )
        counts["denominator"] = len(data)
        counts["percent"] = counts["document_count"] / len(data) * 100
        return counts

    counts = (
        data.groupby([group_column, category_column])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=CATEGORY_ORDER, fill_value=0)
    )
    denominators = counts.sum(axis=1)
    long_counts = (
        counts.reset_index()
        .melt(id_vars=group_column, var_name="category", value_name="document_count")
    )
    long_counts["denominator"] = long_counts[group_column].map(denominators)
    long_counts["percent"] = (
        long_counts["document_count"] / long_counts["denominator"] * 100
    )
    return long_counts


def verify_and_load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    corpus = pd.read_csv(SOURCE / "corpus_final_v2.csv")
    docs = pd.read_csv(SOURCE / "bertopic_docs.csv")
    topics = pd.read_csv(SOURCE / "bertopic_topics.csv")

    assert len(corpus) == 1148, "Unexpected final corpus size"
    assert len(docs) == 985, "Unexpected BERTopic document count"
    assert docs["doc_id"].is_unique, "BERTopic document identifiers are not unique"
    assert set(docs["doc_id"]).issubset(set(corpus["doc_id"]))
    assert set(docs["topic"]) == set(TOPIC_AUDIT)
    retained_counts = topics.set_index("Topic")["Count"].sort_index()
    actual_counts = docs["topic"].value_counts().sort_index()
    pd.testing.assert_series_equal(
        actual_counts,
        retained_counts,
        check_names=False,
        check_dtype=False,
    )
    return corpus, docs, topics


def make_document_flow(corpus: pd.DataFrame, docs: pd.DataFrame) -> pd.DataFrame:
    flow_records = [
        {
            "source": "Nairaland",
            "stage": "Downloaded or scraped raw",
            "document_count": 3473,
            "basis": "raw_posts.json",
        },
        {
            "source": "Nairaland",
            "stage": "Retained by archived cleaning script",
            "document_count": 871,
            "basis": "nairaland_posts.csv",
        },
        {
            "source": "Nairaland",
            "stage": "Included in final corpus",
            "document_count": int((corpus["source"] == "nairaland").sum()),
            "basis": "corpus_final_v2.csv",
        },
        {
            "source": "Nairaland",
            "stage": "Included in BERTopic model",
            "document_count": int((docs["source"] == "nairaland").sum()),
            "basis": "bertopic_docs.csv and minimum eight word rule",
        },
        {
            "source": "Google Play reviews",
            "stage": "Downloaded raw",
            "document_count": 2014,
            "basis": "play_reviews_raw.csv",
        },
        {
            "source": "Google Play reviews",
            "stage": "Included in final corpus",
            "document_count": int((corpus["source"] == "app_review").sum()),
            "basis": "corpus_final_v2.csv; intermediate screening code not retained",
        },
        {
            "source": "Google Play reviews",
            "stage": "Included in BERTopic model",
            "document_count": int((docs["source"] == "app_review").sum()),
            "basis": "bertopic_docs.csv and minimum eight word rule",
        },
        {
            "source": "YouTube",
            "stage": "Downloaded raw",
            "document_count": 1092,
            "basis": "raw_comments.json",
        },
        {
            "source": "YouTube",
            "stage": "Retained by archived cleaning and cap script",
            "document_count": 244,
            "basis": "youtube_comments.csv",
        },
        {
            "source": "YouTube",
            "stage": "Included in final corpus",
            "document_count": int((corpus["source"] == "youtube").sum()),
            "basis": "corpus_final_v2.csv",
        },
        {
            "source": "YouTube",
            "stage": "Included in BERTopic model",
            "document_count": int((docs["source"] == "youtube").sum()),
            "basis": "bertopic_docs.csv and minimum eight word rule",
        },
        {
            "source": "Combined",
            "stage": "Included in final corpus",
            "document_count": len(corpus),
            "basis": "corpus_final_v2.csv",
        },
        {
            "source": "Combined",
            "stage": "Excluded by minimum eight word model rule",
            "document_count": len(corpus) - len(docs),
            "basis": "corpus_final_v2.csv and bertopic_docs.csv",
        },
        {
            "source": "Combined",
            "stage": "Included in BERTopic model",
            "document_count": len(docs),
            "basis": "bertopic_docs.csv",
        },
        {
            "source": "Combined",
            "stage": "BERTopic outliers",
            "document_count": int((docs["topic"] == -1).sum()),
            "basis": "bertopic_docs.csv",
        },
        {
            "source": "Combined",
            "stage": "Assigned to a nonoutlier BERTopic topic",
            "document_count": int((docs["topic"] != -1).sum()),
            "basis": "bertopic_docs.csv",
        },
    ]
    return pd.DataFrame(flow_records)


def build_topic_audit(
    docs: pd.DataFrame, topics: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    audit = (
        pd.DataFrame.from_dict(TOPIC_AUDIT, orient="index")
        .rename_axis("topic")
        .reset_index()
    )
    original = topics[
        ["Topic", "Count", "Name", "Representation", "dimension"]
    ].rename(
        columns={
            "Topic": "topic",
            "Count": "document_count",
            "Name": "original_topic_name",
            "Representation": "original_top_terms",
            "dimension": "original_automatic_dimension",
        }
    )
    audit = original.merge(audit, on="topic", how="right")
    audit["percent_of_all_modelled"] = audit["document_count"] / len(docs) * 100
    nonoutlier_denominator = int((docs["topic"] != -1).sum())
    audit["percent_of_nonoutliers"] = np.where(
        audit["topic"] == -1,
        np.nan,
        audit["document_count"] / nonoutlier_denominator * 100,
    )
    audited_docs = docs.copy()
    audited_docs["original_dimension"] = audited_docs["dimension"]
    audited_docs["audited_category"] = audited_docs["topic"].map(
        {topic: values["audited_category"] for topic, values in TOPIC_AUDIT.items()}
    )
    audited_docs["audit_status"] = np.where(
        audited_docs["original_dimension"].eq(audited_docs["audited_category"]),
        "Unchanged",
        "Changed by documented audit",
    )
    return audit, audited_docs


def build_sensitivity_outputs(audited_docs: pd.DataFrame) -> None:
    source_names = {
        "nairaland": "Nairaland",
        "app_review": "Google Play reviews",
        "youtube": "YouTube",
    }
    sensitivity = audited_docs.copy()
    sensitivity["source_label"] = sensitivity["source"].map(source_names)
    all_source = percent_table(sensitivity, "source_label")
    all_source.to_csv(OUT / "source_sensitivity_all_modelled.csv", index=False)

    nonoutliers = sensitivity[sensitivity["audited_category"] != "Outlier"].copy()
    percent_table(nonoutliers, "source_label").to_csv(
        OUT / "source_sensitivity_nonoutliers.csv", index=False
    )

    mapped = nonoutliers[
        nonoutliers["audited_category"] != "Residual or mixed"
    ].copy()
    percent_table(mapped, "source_label").to_csv(
        OUT / "source_sensitivity_substantively_mapped.csv", index=False
    )

    dominant_origin = audited_docs["origin"].value_counts().index[0]
    without_dominant = audited_docs[audited_docs["origin"] != dominant_origin].copy()
    comparisons = []
    for label, frame in [
        ("All modelled documents", audited_docs),
        ("Excluding dominant origin", without_dominant),
        (
            "Nairaland excluding dominant origin",
            without_dominant[without_dominant["source"] == "nairaland"],
        ),
    ]:
        summary = percent_table(frame)
        summary.insert(0, "sensitivity_scenario", label)
        summary.insert(1, "excluded_origin", dominant_origin if "excluding" in label.lower() else "")
        comparisons.append(summary)
    pd.concat(comparisons, ignore_index=True).to_csv(
        OUT / "dominant_origin_sensitivity.csv", index=False
    )


def build_validation_sample(audited_docs: pd.DataFrame) -> None:
    sample_parts = []
    nonoutlier_topics = [topic for topic in sorted(TOPIC_AUDIT) if topic != -1]
    for topic in nonoutlier_topics:
        # A topic-stratified sample tests the manual topic-to-category audit.
        # Nine documents are selected from each of the eleven topics, with one
        # additional document from the largest substantive topic, for n = 100.
        sample_size = 10 if topic == 0 else 9
        topic_documents = audited_docs[audited_docs["topic"] == topic]
        if len(topic_documents) < sample_size:
            raise ValueError(f"Topic {topic} has fewer than {sample_size} documents")
        sample_parts.append(
            topic_documents.sample(
                n=sample_size,
                random_state=4200 + topic,
                replace=False,
            )
        )
    sample = (
        pd.concat(sample_parts, ignore_index=True)
        .sample(frac=1, random_state=42)
        .reset_index(drop=True)
    )
    sample.insert(0, "validation_id", [f"VAL{index:03d}" for index in range(1, len(sample) + 1)])
    sample[
        [
            "validation_id",
            "doc_id",
            "source",
            "origin",
            "text",
            "word_count",
            "topic",
            "audited_category",
        ]
    ].to_csv(OUT / "human_validation_sample.csv", index=False)


def tfidf_stability(docs: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    stop_words = sorted(set(ENGLISH_STOP_WORDS).union(EXTRA_STOP_WORDS))
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words=stop_words,
        ngram_range=(1, 2),
        min_df=3,
        max_df=0.95,
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(docs["text"].fillna(""))
    seeds = [0, 21, 42, 84, 123]
    records = []
    for k in range(5, 16):
        label_runs = []
        silhouettes = []
        inertias = []
        minimum_sizes = []
        for seed in seeds:
            model = KMeans(
                n_clusters=k,
                random_state=seed,
                n_init=20,
                max_iter=500,
                algorithm="lloyd",
            )
            labels = model.fit_predict(matrix)
            label_runs.append(labels)
            silhouettes.append(silhouette_score(matrix, labels, metric="cosine"))
            inertias.append(model.inertia_)
            minimum_sizes.append(int(np.bincount(labels).min()))
        pairwise_ari = [
            adjusted_rand_score(left, right)
            for left, right in combinations(label_runs, 2)
        ]
        records.append(
            {
                "cluster_count": k,
                "mean_cosine_silhouette": float(np.mean(silhouettes)),
                "standard_deviation_cosine_silhouette": float(np.std(silhouettes)),
                "mean_pairwise_adjusted_rand_index": float(np.mean(pairwise_ari)),
                "minimum_pairwise_adjusted_rand_index": float(np.min(pairwise_ari)),
                "mean_inertia": float(np.mean(inertias)),
                "median_smallest_cluster_size": float(np.median(minimum_sizes)),
                "selection_note": (
                    "Selected for the diagnostic baseline because it had the highest "
                    "cross seed stability among the evaluated values."
                    if k == 5
                    else ""
                ),
            }
        )

    stability = pd.DataFrame(records)
    final_model = KMeans(
        n_clusters=5,
        random_state=42,
        n_init=50,
        max_iter=500,
        algorithm="lloyd",
    )
    labels = final_model.fit_predict(matrix)
    assignments = docs[
        ["doc_id", "source", "origin", "text", "word_count"]
    ].copy()
    assignments["tfidf_cluster"] = labels

    terms = np.asarray(vectorizer.get_feature_names_out())
    descriptive_labels = {
        0: "Office location and registration",
        1: "Mixed service, payment, and health discussion",
        2: "HMO comparison and trust",
        3: "NHIS coverage and provider access",
        4: "Login and registration",
    }
    cluster_rows = []
    for cluster in range(5):
        center = final_model.cluster_centers_[cluster]
        top_terms = terms[np.argsort(center)[::-1][:12]]
        members = assignments[assignments["tfidf_cluster"] == cluster]
        source_counts = members["source"].value_counts()
        cluster_rows.append(
            {
                "tfidf_cluster": cluster,
                "descriptive_label": descriptive_labels[cluster],
                "document_count": len(members),
                "percent_of_modelled_documents": len(members) / len(assignments) * 100,
                "top_terms": "; ".join(top_terms.tolist()),
                "nairaland_count": int(source_counts.get("nairaland", 0)),
                "app_review_count": int(source_counts.get("app_review", 0)),
                "youtube_count": int(source_counts.get("youtube", 0)),
                "interpretive_status": (
                    "Mixed cluster; not suitable for category prevalence claims"
                    if cluster == 1
                    else "Descriptive cluster only; human validation required"
                ),
            }
        )
    cluster_summary = pd.DataFrame(cluster_rows)

    model_diagnostics = pd.DataFrame(
        [
            {
                "model": "TF IDF plus k means diagnostic baseline",
                "documents": len(assignments),
                "features": matrix.shape[1],
                "selected_cluster_count": 5,
                "random_seed": 42,
                "n_init": 50,
                "inertia": final_model.inertia_,
                "cosine_silhouette": silhouette_score(
                    matrix, labels, metric="cosine"
                ),
                "interpretation": (
                    "Very weak separation. The baseline is retained as a sensitivity "
                    "diagnostic and does not validate BERTopic category rankings."
                ),
            }
        ]
    )
    return stability, assignments, cluster_summary.merge(
        model_diagnostics.assign(key=1), how="cross"
    ).drop(columns="key")


def configure_plot_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.labelsize": 10,
            "axes.titlesize": 11,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )


def plot_overall(summary: pd.DataFrame) -> None:
    configure_plot_style()
    ordered = summary.set_index("category").reindex(CATEGORY_ORDER).reset_index()
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    bars = ax.barh(
        ordered["category"],
        ordered["percent"],
        color=[CATEGORY_COLORS[value] for value in ordered["category"]],
        edgecolor="white",
    )
    ax.invert_yaxis()
    ax.set_xlabel("Percentage of all modelled documents")
    ax.set_xlim(0, max(40, ordered["percent"].max() + 6))
    ax.grid(axis="x", alpha=0.2)
    for bar, count, value in zip(
        bars, ordered["document_count"], ordered["percent"]
    ):
        ax.text(
            bar.get_width() + 0.5,
            bar.get_y() + bar.get_height() / 2,
            f"{int(count)}  ({value:.1f}%)",
            va="center",
            fontsize=9,
        )
    fig.tight_layout()
    fig.savefig(OUT / "figure_overall_audited_distribution.png", dpi=300)
    fig.savefig(OUT / "figure_overall_audited_distribution.svg")
    plt.close(fig)


def plot_source_sensitivity(source_summary: pd.DataFrame) -> None:
    configure_plot_style()
    pivot = (
        source_summary.pivot(
            index="source_label", columns="category", values="percent"
        )
        .reindex(["Nairaland", "Google Play reviews", "YouTube"])
        .reindex(columns=CATEGORY_ORDER, fill_value=0)
    )
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    left = np.zeros(len(pivot))
    for category in CATEGORY_ORDER:
        values = pivot[category].to_numpy()
        ax.barh(
            pivot.index,
            values,
            left=left,
            label=category,
            color=CATEGORY_COLORS[category],
            edgecolor="white",
        )
        for index, value in enumerate(values):
            if value >= 7:
                ax.text(
                    left[index] + value / 2,
                    index,
                    f"{value:.0f}%",
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="white" if category in {"Procedural access", "Trust and reliability"} else "black",
                )
        left += values
    ax.set_xlabel("Percentage within source")
    ax.set_xlim(0, 100)
    ax.invert_yaxis()
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=3,
        frameon=False,
        fontsize=8,
    )
    fig.tight_layout()
    fig.savefig(OUT / "figure_source_sensitivity.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "figure_source_sensitivity.svg", bbox_inches="tight")
    plt.close(fig)


def plot_tfidf_stability(stability: pd.DataFrame) -> None:
    configure_plot_style()
    fig, left_ax = plt.subplots(figsize=(8.4, 4.3))
    right_ax = left_ax.twinx()
    left_ax.plot(
        stability["cluster_count"],
        stability["mean_cosine_silhouette"],
        marker="o",
        color="#1F4E79",
        label="Mean cosine silhouette",
    )
    right_ax.plot(
        stability["cluster_count"],
        stability["mean_pairwise_adjusted_rand_index"],
        marker="s",
        color="#C55A11",
        label="Mean pairwise adjusted Rand index",
    )
    left_ax.axvline(5, color="#7F7F7F", linestyle=":", linewidth=1)
    left_ax.set_xlabel("Number of clusters")
    left_ax.set_ylabel("Mean cosine silhouette", color="#1F4E79")
    right_ax.set_ylabel("Mean adjusted Rand index", color="#C55A11")
    left_ax.set_xticks(stability["cluster_count"])
    left_ax.grid(axis="y", alpha=0.2)
    lines = left_ax.get_lines()[:1] + right_ax.get_lines()
    labels = [line.get_label() for line in lines]
    left_ax.legend(lines, labels, loc="upper left", frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "figure_tfidf_stability.png", dpi=300)
    fig.savefig(OUT / "figure_tfidf_stability.svg")
    plt.close(fig)


def write_manifest() -> None:
    source_files = {
        "corpus_final_v2.csv": SOURCE / "corpus_final_v2.csv",
        "bertopic_docs.csv": SOURCE / "bertopic_docs.csv",
        "bertopic_topics.csv": SOURCE / "bertopic_topics.csv",
        "bertopic_dimensions.csv": SOURCE / "bertopic_dimensions.csv",
        "04_bertopic_COLAB.py": SOURCE / "04_bertopic_COLAB.py",
        "Untitled2.ipynb": SOURCE / "Untitled2.ipynb",
        "MIT8212_Seminar_Paper.docx": SOURCE / "MIT8212_Seminar_Paper.docx",
        "fig_dimensions_v2.png": ORIGINAL_TFIDF_FIGURE,
    }
    manifest = {
        "purpose": (
            "Reconstruction and audit of the researcher-created seminar analysis. "
            "This does not claim to reproduce the original software environment."
        ),
        "source_file_hashes": {
            name: sha256(path) for name, path in source_files.items()
        },
        "reconstruction_environment": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "important_limitations": [
            "The original TF IDF trial is evidenced by its figure and contemporaneous narrative, but its code, assignments, parameters, and corrected mapping were not retained.",
            "The original package versions were not recorded.",
            "The record-level corpus assembly code and screening log were not retained.",
            "The audited topic mapping requires independent human validation before it can be described as validated.",
        ],
    }
    (OUT / "reconstruction_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


def main() -> None:
    corpus, docs, topics = verify_and_load()
    document_flow = make_document_flow(corpus, docs)
    document_flow.to_csv(OUT / "document_flow.csv", index=False)

    topic_audit, audited_docs = build_topic_audit(docs, topics)
    topic_audit.to_csv(OUT / "topic_audit.csv", index=False)
    audited_docs.to_csv(
        OUT / "bertopic_document_assignments_audited.csv", index=False
    )

    overall_all = percent_table(audited_docs)
    overall_all.to_csv(
        OUT / "category_summary_all_modelled.csv", index=False
    )
    nonoutliers = audited_docs[
        audited_docs["audited_category"] != "Outlier"
    ].copy()
    percent_table(nonoutliers).to_csv(
        OUT / "category_summary_nonoutliers.csv", index=False
    )
    mapped = nonoutliers[
        nonoutliers["audited_category"] != "Residual or mixed"
    ].copy()
    percent_table(mapped).to_csv(
        OUT / "category_summary_substantively_mapped.csv", index=False
    )

    build_sensitivity_outputs(audited_docs)
    build_validation_sample(audited_docs)
    source_summary = pd.read_csv(OUT / "source_sensitivity_all_modelled.csv")

    stability, tfidf_assignments, tfidf_clusters = tfidf_stability(docs)
    stability.to_csv(OUT / "tfidf_kmeans_stability.csv", index=False)
    tfidf_assignments.to_csv(
        OUT / "tfidf_kmeans_assignments_k5_seed42.csv", index=False
    )
    tfidf_clusters.to_csv(OUT / "tfidf_kmeans_cluster_summary.csv", index=False)

    plot_overall(overall_all)
    plot_source_sensitivity(source_summary)
    plot_tfidf_stability(stability)
    write_manifest()

    summary = {
        "final_corpus_documents": len(corpus),
        "modelled_documents": len(docs),
        "outliers": int((docs["topic"] == -1).sum()),
        "nonoutliers": int((docs["topic"] != -1).sum()),
        "audited_category_counts_all_modelled": {
            row["category"]: int(row["document_count"])
            for _, row in overall_all.iterrows()
        },
        "dominant_origin": audited_docs["origin"].value_counts().index[0],
        "dominant_origin_modelled_documents": int(
            audited_docs["origin"].value_counts().iloc[0]
        ),
    }
    (OUT / "analysis_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
