# Research and computational provenance

## Research workflow

1. The researcher began with Nigerian insurance application reviews. An initial Python discovery script ran in Google Colab with 30 search queries and returned 93 unique candidates. Only 14 of the 24 applications ultimately retained were present, and unrelated applications dominated the apparent review total.

2. A second Google Play discovery script expanded coverage to 110 queries and returned 301 unique candidates. Its keyword rule flagged 86 likely matches. Manual review retained 24 consumer applications, reversing 62 automatic true flags and adding no candidates. The review downloader then collected 2,014 records from those 24 applications.

3. Because the application review route produced limited relevant material, the researcher expanded collection to Nairaland. JavaScript scripts running with Node.js discovered relevant threads, followed pagination, extracted post text, and cleaned the output.

4. The researcher then expanded collection to YouTube insurance videos. JavaScript scripts running with Node.js used the YouTube Data API to discover videos, retrieve available comments and replies, and clean the output. A standard API key was created in Google Cloud Console after the API was enabled and was loaded from a local environment file.

5. The Nairaland and YouTube scraping stages were executed through Claude Code on the researcher’s computer.

6. The three cleaned source outputs were standardised and combined into `corpus_final_v2.csv`. The final file is retained, but the record level assembly code and decision log were not preserved.

7. The researcher uploaded the final corpus, ran the BERTopic script in Google Colab, and retained `bertopic_dimensions.csv`, `bertopic_topics.csv`, and `bertopic_docs.csv`.

8. The original TF IDF with K means analysis was performed in Claude Chat. The returned `fig_dimensions_v2.png` and method note identify a 25.5 per cent NHIS registration cluster that the keyword mapper incorrectly labelled Premium or Pricing. The underlying original code, assignments, parameters, and corrected mapping were not retained.

9. A transparent TF IDF rerun was then performed on the same 985 modelled text items. The rerun records vectorisation settings, random seeds, cluster stability, final assignments, and cluster interpretation.

## Audit interpretation

The original TF IDF figure proves that the comparison was performed. It does not provide reproducible confirmation because its dominant category was acknowledged as mislabelled and the analytical artefacts needed to correct the result are absent.

The correction audit therefore preserves the original figure as provenance evidence and separately provides a reproducible transparent TF IDF rerun. The rerun has weak separation and is not presented as confirmation of the BERTopic category ranking.

The researcher remains responsible for the research question, source selection, execution decisions, interpretation, and final academic submission.

The intertopic map and topic bar chart are retained as interactive interpretation aids. They show topic proximity, size, and representative words, but they do not independently validate the reviewed topic labels.
