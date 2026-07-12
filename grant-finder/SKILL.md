---
name: grant-finder
description: "Research grant discovery and ranking agent. 7-agent pipeline for discovering, scoring, and prioritizing NIH/HHS funding opportunities relevant to computational and data-science research. 3 modes: search (live NIH Guide + Grants.gov ingestion), digest (saved results report), context (NIH RePORTER funded-project lookup). Multi-source ingestion, explainable relevance scoring (0-100), classification tiers (HIGH/MEDIUM/WATCHLIST), SQLite persistence, Excel export, interactive Streamlit dashboard. Triggers on: find grants, NIH grants, funding opportunities, grant search, research funding, grant matcher, grant finder, 找補助, 補助金, 研究經費, NIH 補助."
metadata:
  version: "1.0.0"
  last_updated: "2026-07-12"
  status: active
  data_access_level: raw
  task_type: open-ended
  related_skills:
    - deep-research
    - academic-pipeline
---

# Grant Finder — Research Grant Discovery & Ranking Agent Team

A domain-focused grant discovery tool — a 7-agent team for finding, scoring, and prioritizing NIH/HHS funding opportunities relevant to computational and data-science research.

Based on [Quazi-07/Research-Grant-Finder-Agent](https://github.com/Quazi-07/Research-Grant-Finder-Agent).

> **Routing discipline (v3.9.2):** see `.claude/CLAUDE.md` "Routing Discipline (v3.9.2)" for cross-skill routing rules. This skill handles funding discovery only — for research, writing, or review, route to the appropriate skill.

## Quick Start

**Minimal command (CLI):**
```
cd grant-finder
python -m nih_grant_matcher run --source nih-guide --keyword "machine learning"
```

**Interactive dashboard:**
```
cd grant-finder
streamlit run streamlit_app.py
```

**Python API:**
```python
from nih_grant_matcher.config import MatcherConfig
from nih_grant_matcher.workflow import run_and_save

config = MatcherConfig(rows=100, db_path="data/grants.sqlite3")
scored_items, summary = run_and_save(config, source="nih-guide", keyword="deep learning")
for item in scored_items[:5]:
    print(f"{item.classification}: {item.score:.1f} — {item.opportunity.title}")
```

---

## Trigger Conditions

### Trigger Keywords

**English**: find grants, NIH grants, funding opportunities, grant search, research funding, grant matcher, grant finder, NIH funding, computational grants, ML grants, data science funding

**繁體中文**: 找補助, 補助金, 研究經費, NIH 補助, 研究資助, 科研經費

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Researching a topic (not finding grants) | `deep-research` |
| Writing a grant proposal (paper) | `academic-paper` |
| Reviewing a paper | `academic-paper-reviewer` |
| Full research-to-paper pipeline | `academic-pipeline` |

---

## Mode Selection Guide

| Your Situation | Recommended Mode | Spectrum |
|----------------|-----------------|----------|
| Need to discover new NIH funding opportunities | `search` | Fidelity |
| Want a report from previously saved results | `digest` | Fidelity |
| Need context on funded projects in a research area | `context` | Fidelity |

---

## Agent Team (7 Agents)

| # | Agent | Role | Phase |
|---|-------|------|-------|
| 1 | `nih_guide_ingestion_agent` | Discovers and normalizes NIH Guide funding announcements | Phase 1 (Ingestion) |
| 2 | `grantsgov_ingestion_agent` | Searches and enriches federal opportunities from Grants.gov | Phase 1 (Ingestion) |
| 3 | `grant_parser_agent` | Converts heterogeneous records into a unified opportunity model | Phase 1 (Normalization) |
| 4 | `ml_relevance_agent` | Evaluates computational/data-science relevance via multi-signal scoring | Phase 2 (Scoring) |
| 5 | `nih_context_agent` | Retrieves funded-project context from NIH RePORTER | Phase 2 (Context) |
| 6 | `digest_agent` | Generates prioritized Markdown intelligence reports | Phase 3 (Output) |
| 7 | `review_feedback_agent` | Captures researcher assessments for future tuning | Phase 3 (Feedback) |

---

## Orchestration Workflow (3 Phases)

```
User: "Find NIH grants for [topic]"
     |
=== Phase 1: INGESTION ===
     |
     |-> [nih_guide_ingestion_agent] -> Raw NIH Guide records
     |   - Paginated search of NIH Guide API
     |   - Normalizes to Opportunity model
     |
     |-> [grantsgov_ingestion_agent] -> Raw Grants.gov records
     |   - Paginated search + detail enrichment
     |   - [grant_parser_agent] normalizes each record
     |
     +-> Deduplication (opportunity_number key, NIH Guide preferred)
     |
=== Phase 2: SCORING ===
     |
     |-> [ml_relevance_agent] -> ScoredOpportunity[]
     |   - Keyword detection (AI, ML, bioinformatics, etc.)
     |   - Title centrality weighting
     |   - Semantic similarity to curated examples
     |   - NIH/HHS source bonus
     |   - Deadline awareness scoring
     |   - Record completeness scoring
     |   - Generic biomedical noise penalty
     |   - Classification: HIGH (>=70) / MEDIUM (>=45) / WATCHLIST (<45)
     |
     |-> [nih_context_agent] (optional) -> Similar funded projects
     |   - NIH RePORTER search for related awards
     |
     +-> Filter: current NIH/HHS opportunities only
     |
=== Phase 3: OUTPUT ===
     |
     |-> SQLite persistence (upsert)
     |-> [digest_agent] -> Markdown intelligence report
     |-> Excel export (optional)
     |-> Streamlit dashboard (optional)
     |
     +-> [review_feedback_agent] (optional)
         - Records researcher useful/not-useful + notes per opportunity
```

---

## Scoring System

### Score Components

| Component | Max Points | Description |
|-----------|-----------|-------------|
| Keyword detection | ~50 | Weighted matches for 24 computational terms |
| Semantic similarity | 20 | Cosine similarity to 6 curated ML/data-science examples |
| Title centrality | 18 | Higher weight for terms appearing in the title |
| NIH/HHS source | 10 | Bonus for confirmed NIH/HHS agency |
| Deadline awareness | 8 | Active deadlines (14-90 days out) score highest |
| Completeness | 7 | More complete records score higher |
| Generic penalty | -10 to -40 | Reduces score for generic biomedical wording |

### Classification Tiers

| Tier | Score Range | Meaning |
|------|------------|---------|
| HIGH | >= 70 | Strong AI/ML/computational relevance evidence |
| MEDIUM | >= 45 | Interdisciplinary data-science collaboration potential |
| WATCHLIST | < 45 | Weak emerging computational signals |

---

## Data Sources

| Source | API | Auth Required |
|--------|-----|---------------|
| NIH Guide for Grants and Contracts | Elasticsearch API | No |
| Grants.gov | REST API v1 | No |
| NIH RePORTER | REST API v2 | No |

---

## CLI Reference

```bash
# Fetch, score, save, and write a Markdown digest
python -m nih_grant_matcher run \
    --source nih-guide \
    --keyword "machine learning" \
    --limit 250 \
    --out digests/latest.md

# Write a digest from saved opportunities
python -m nih_grant_matcher digest --min-score 45 --limit 50

# Export to Excel
python -m nih_grant_matcher excel --out results.xlsx --min-score 45

# Search NIH RePORTER for funded project context
python -m nih_grant_matcher reporter-context --term "clinical prediction" --limit 10

# Download latest Grants.gov XML extract
python -m nih_grant_matcher backfill-xml --out data/latest.zip
```

---

## Dependencies

- Python 3.10+
- `streamlit >= 1.36` (dashboard only)
- `pandas >= 2.0` (dashboard only)
- No API keys required — all data sources are public

---

## Integration with ARS Pipeline

Grant Finder is a **pre-pipeline discovery tool**. Typical workflow:

1. **Grant Finder** discovers relevant funding opportunities
2. User selects a target opportunity
3. **deep-research** investigates the topic area
4. **academic-paper** drafts the grant proposal/paper
5. **academic-paper-reviewer** reviews the draft

The grant finder does not feed directly into the pipeline — it produces a ranked list of opportunities for human selection. The selected opportunity's description and requirements then inform the research direction.

---

## Disclaimer

Not affiliated with NIH, Grants.gov, or HHS. Users must independently verify eligibility, deadlines, requirements, and scope using official announcements.
