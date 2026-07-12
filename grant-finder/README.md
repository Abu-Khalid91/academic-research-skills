# Research Grant Finder Agent

An intelligent system for discovering and prioritizing NIH funding opportunities. Transforms fragmented public funding data into actionable research intelligence by combining multi-source ingestion, computational relevance scoring, and explainable ranking.

Based on [Quazi-07/Research-Grant-Finder-Agent](https://github.com/Quazi-07/Research-Grant-Finder-Agent).

## Architecture

Six specialized agents orchestrate the discovery pipeline:

| Agent | Role |
|-------|------|
| NIH Guide Ingestion | Discovers and normalizes NIH funding announcements |
| Grants.gov Ingestion | Searches and enriches federal opportunities |
| Grant Parser | Converts heterogeneous records into a unified opportunity model |
| ML Relevance | Evaluates computational/data-science relevance via scoring |
| NIH Context | Retrieves funded-project context from NIH RePORTER |
| Digest | Generates prioritized intelligence reports |
| Review Feedback | Captures researcher assessments for future tuning |

## Scoring

Opportunities are scored 0-100 across multiple dimensions:

- **Keyword detection** (AI, ML, bioinformatics, imaging, statistical modeling)
- **Title centrality weighting** (terms in the title score higher)
- **Semantic similarity** to curated ML/data-science grant examples
- **NIH/HHS source** bonus
- **Deadline awareness** (active deadlines prioritized)
- **Record completeness**
- **Generic biomedical penalty** (reduces noise from non-computational grants)

Classification tiers: **HIGH** (>=70), **MEDIUM** (>=45), **WATCHLIST** (<45).

## Quick Start

```bash
cd grant-finder
pip install -e .

# CLI: fetch, score, and generate a digest
python -m nih_grant_matcher run --source nih-guide --keyword "machine learning"

# CLI: export to Excel
python -m nih_grant_matcher excel --out results.xlsx

# Interactive dashboard
streamlit run streamlit_app.py
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `run` | Fetch, score, save, and write a Markdown digest |
| `digest` | Write a digest from previously saved opportunities |
| `excel` | Export saved ranked opportunities to `.xlsx` |
| `reporter-context` | Search NIH RePORTER for funded project context |
| `backfill-xml` | Download the latest Grants.gov XML extract |

## Tests

```bash
cd grant-finder
pytest
```

## Data Sources

- [NIH Guide for Grants and Contracts](https://grants.nih.gov/funding/nih-guide-for-grants-and-contracts)
- [Grants.gov](https://www.grants.gov/)
- [NIH RePORTER](https://reporter.nih.gov/)

## Disclaimer

Not affiliated with NIH, Grants.gov, or HHS. Users must independently verify eligibility, deadlines, requirements, and scope using official announcements.
