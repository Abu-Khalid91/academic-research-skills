# Scoring Protocol — ML Relevance Scoring

## Overview

The ML Relevance Scorer evaluates each funding opportunity for computational and data-science relevance using a deterministic, explainable multi-signal scoring system. No LLM inference is used — all scoring is rule-based for transparency and reproducibility.

## Score Formula

```
score = clamp(0, 100,
    keyword_score
    + semantic_score
    + nih_score
    + urgency_score
    + completeness_score
    + min(centrality_score, 18)
    - generic_penalty
)
```

## Signal Details

### 1. Keyword Detection (keyword_score)

24 computational terms with manually assigned weights (6-18 points each). Matching is case-insensitive substring search against `searchable_text` (title + description + eligibility + funding instruments + funding categories + agency name).

Special handling: standalone `AI` uses word-boundary regex (`\bai\b`) to avoid false positives from words containing "ai".

### 2. Title Centrality (centrality_score, capped at 18)

Terms found in the title receive higher centrality scores than those found only in the description:
- Title match: `weight * 0.8` (capped at 12 per term)
- Description-only match: `weight * 0.25` (capped at 4 per term)

### 3. Semantic Similarity (semantic_score, max 20)

Cosine similarity between the opportunity's term-frequency vector and 6 curated ML/data-science grant example sentences. Uses bag-of-words TF vectors (alphanumeric tokens, lowercased). Best match across examples is scaled by 80 and capped at 20.

### 4. NIH/HHS Source Bonus (nih_score, 0 or 10)

10 points if agency_code or agency_name contains "NIH", "National Institutes of Health", or "HHS".

### 5. Deadline Awareness (urgency_score)

| Days until close | Score |
|-----------------|-------|
| No deadline | 3.0 |
| Expired (< 0) | -20.0 |
| <= 14 days | 4.0 |
| <= 90 days | 8.0 |
| <= 240 days | 6.0 |
| > 240 days | 3.0 |

### 6. Record Completeness (completeness_score, max 7)

Proportion of non-empty fields among: description, close_date, eligibility, funding_instruments, funding_categories, award_ceiling, source_url. Scaled to max 7 points.

### 7. Generic Biomedical Penalty (generic_penalty)

Counts matches against 8 generic biomedical terms: "clinical trial", "health disparities", "community health", "training program", "capacity building", "implementation", "prevention", "therapeutic".

- With computational terms: `max(0, generic_hits * 2 - len(matched_terms))`
- Without computational terms: `generic_hits * 5`

## Classification

| Tier | Score Range | Color |
|------|------------|-------|
| HIGH | >= 70 | Red |
| MEDIUM | >= 45 | Orange |
| WATCHLIST | < 45 | Yellow |
