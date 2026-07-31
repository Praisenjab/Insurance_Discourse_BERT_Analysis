# Insurance comprehension gaps in Nigerian online discourse

This repository supports a seminar paper by Praise Ejama Njab. The study analyses selected public Nairaland posts and replies, Google Play insurance application reviews, and YouTube comments using BERTopic and TF IDF with K means. The findings are then converted into requirements for a proposed governed retrieval augmented generation knowledge system.

The seminar delivers a research and system design blueprint. It does not claim that the RAG application has already been implemented or evaluated.

## 1. Research workflow

1. Discover and collect selected Nigerian insurance related text from Google Play, Nairaland, and YouTube.

2. Clean and combine the retained source records into a 1,148 item corpus.

3. Apply the eight word minimum and model 985 items with BERTopic.

4. Review all eleven BERTopic topics and report 302 outliers rather than hiding them.

5. Compare the findings with the retained original TF IDF output and a transparent TF IDF and K means rerun.

6. Test variation across sources and after removing the dominant Nairaland discussion.

7. Convert the evidence and its limitations into system requirements, RAG architecture, safeguards, governance controls, and an evaluation plan.

## 2. Verified dataset flow

| Source or stage | Retained count |
|---|---:|
| Nairaland raw posts and replies | 3,473 |
| Nairaland after archived cleaning | 871 |
| Nairaland in final corpus | 654 |
| Google Play raw reviews | 2,014 |
| Google Play reviews in final corpus | 277 |
| YouTube raw comments and replies | 1,092 |
| YouTube after archived cleaning and cap | 244 |
| YouTube comments in final corpus | 217 |
| Combined final corpus | 1,148 |
| Items modelled with BERTopic | 985 |
| BERTopic nonoutlier items | 683 |
| BERTopic outliers | 302 |

The record level decisions for Google Play 2,014 to 277, Nairaland 871 to 654, YouTube 244 to 217, and final corpus assembly were not retained. The repository does not invent those missing decisions.

## 3. Google Play discovery history

| Stage | Queries | Candidate applications | Outcome |
|---|---:|---:|---|
| Initial pilot | 30 | 93 | Found 14 of the 24 applications eventually retained, but unrelated applications dominated the apparent review volume. |
| Expanded discovery | 110 | 301 | Automatically flagged 86 likely matches and found all 24 applications eventually retained. |
| Manual review | Same 301 candidates | 24 retained | Changed 62 automatic true flags to false and added no candidates. |

The metadata in `app_candidates_v2.csv` and `app_candidates_v3.csv` match exactly. The final file records the researcher reviewed retention and role decisions.

## 4. Repository contents

| Path | Purpose |
|---|---|
| `collection/google_play/` | Initial discovery, expanded discovery, and review download scripts plus candidate metadata. |
| `collection/nairaland/` | Thread discovery, scraping, and archived cleaning scripts. The retained package metadata lists Cheerio, but the scripts use regular expressions and the native Fetch API rather than importing Cheerio. |
| `collection/youtube/` | Video discovery, comment extraction, cleaning scripts, and a safe environment variable example. |
| `analysis/04_bertopic_COLAB.py` | Retained BERTopic model script executed by the researcher in Google Colab. |
| `analysis/rebuild_analysis.py` | Transparent audit, sensitivity analysis, and TF IDF rerun. |
| Root CSV and JSON files | Aggregate tables, manifests, reviewed mappings, and comparison evidence used in the paper. |
| `excel_figures/` and `MIT8212_Analysis_Charts.xlsx` | The seven Excel styled paper figures and the editable chart workbook. |
| `docs/` | Interactive BERTopic map, topic bar chart, and GitHub Pages index. |
| `PROVENANCE.md` | What was originally retained, what was reconstructed, and what remains unavailable. |

## 5. Reproducing the collection stages

Live platform content changes, so a later collection run will not recreate the exact July 2026 records. These instructions reproduce the documented logic and generate a new time specific output.

### Google Play in Google Colab

1. Run `01_check_apps_COLAB.py` to reproduce the initial 30 query pilot and create `app_candidates.csv`.

2. Run `01b_discover_expanded_COLAB.py` to reproduce the expanded 110 query discovery and create `app_candidates_v2.csv`.

3. Review every candidate and record the final `keep` and `role` decisions in `app_candidates_v3.csv`. Do not treat the automatic keyword flag as a final inclusion decision.

4. Upload the reviewed file and run `02b_download_reviews_COLAB.py`. The script creates `play_reviews_raw.csv`.

### Nairaland with Node.js

Run the scripts from their own folder so their relative input and output paths resolve correctly:

```bash
cd collection/nairaland
npm ci
node discover.js
node scrape.js
node clean.js
```

The expected sequence is `threads.json`, `raw_posts.json`, and `nairaland_posts.csv`. The retained scripts use the native Fetch API and regular expressions. Respect the site rules and retain the built in request delays.

### YouTube with Node.js

Create and restrict an API key using the official [YouTube Data API instructions](https://developers.google.com/youtube/v3/getting-started) and [Google Cloud API key guidance](https://cloud.google.com/docs/authentication/api-keys). Copy `.env.example` to a local `.env` file, replace the placeholder locally, and never commit that file.

```bash
cd collection/youtube
npm ci
node discover.js
node scrape_comments.js
node clean.js
```

The expected sequence is `videos.json`, `raw_comments.json`, and `youtube_comments.csv`. A later run depends on current video availability, comment settings, API quota, and live platform content.

## 6. Running the transparent analysis

The original text files are not published in the public repository. An authorised examiner or researcher with the private source files should place these files in `source/seminar files/`:

```text
corpus_final_v2.csv
bertopic_docs.csv
bertopic_topics.csv
bertopic_dimensions.csv
04_bertopic_COLAB.py
Untitled2.ipynb
MIT8212_Seminar_Paper.docx
fig_dimensions_v2.png
```

Create a Python environment and install the recorded audit packages:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-audit.txt
python analysis/rebuild_analysis.py
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

The script checks the expected corpus and topic counts before producing the audit tables, sensitivity results, transparent TF IDF rerun, and reconstruction manifest.

## 7. Original and reproduction environments

The original Google Colab and Node.js package versions were not pinned. They must not be guessed.

The later transparent audit environment was:

| Component | Version |
|---|---:|
| Python | 3.12.13 |
| pandas | 2.2.3 |
| NumPy | 2.3.5 |
| scikit learn | 1.8.0 |

These versions describe the correction audit, not the original BERTopic run.

## 8. Interactive BERTopic outputs

Open `docs/index.html` locally or enable GitHub Pages from the `docs` folder.

1. The intertopic distance map shows topic size and relative semantic proximity. Its axes have no direct substantive meaning.

2. The topic bar chart ranks the strongest class based TF IDF terms for each topic. It supports interpretation but does not validate a topic label.

The reviewed topic decisions in `topic_audit.csv` remain the primary interpretation record.

## 9. Credentials and publication safety

The YouTube scripts used a standard API key created in Google Cloud Console after the YouTube Data API v3 was enabled. Never commit the original `.env` file or any API key.

1. Copy `.env.example` to `.env` only on the local computer.

2. Restrict the key to the YouTube Data API and to the intended application or IP where practical.

3. Rotate the original key before publishing because it appeared in the private source archive.

4. Confirm that `.env`, raw text files, notebook account details, local paths, and private links are absent before every push.

## 10. Data availability and ethics

The public repository excludes raw posts, reviews, comments, API credentials, and text item level model assignments. This reduces unnecessary republication of identifiable public text. Aggregate outputs and scripts are included. The private research archive may be shared with an examiner under appropriate access controls.

## 11. Interpretation limits

1. The sources represent selected digitally engaged contributors, not all Nigerian consumers.

2. Health insurance and one Nairaland discussion are heavily represented.

3. The BERTopic mapping remains provisional until independent coding is completed.

4. The original TF IDF analysis was performed in Claude Chat and returned a figure and narrative, but no executable original code or assignments were retained.

5. The transparent TF IDF rerun has weak cluster separation and does not confirm a universal BERTopic ranking.

6. The proposed RAG system has not yet been implemented or tested.

## 12. Design provenance

The proposed system is an original synthesis rather than a copy of one existing application. Design Science Research Methodology structures the design process. Retrieval augmented generation supplies the retrieval and answer generation pattern. Nigerian insurance, health insurance, market conduct, insurtech, and data protection instruments inform governance. BERTopic, TF IDF, and source sensitivity findings determine the priority consumer tasks and safeguards.

## 13. Author

Praise Ejama Njab  
Master of Information Technology, Information Management Systems  
MIVA Open University
