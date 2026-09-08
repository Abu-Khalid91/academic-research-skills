---
name: research-pulse
description: "On-demand research-trends and business-insight digest. 2 modes: scan (broad multi-bucket live search across AI/LLM research trends, the user's active research domain, academic-research-tooling trends, and business/monetization trends, synthesized into a dated, cited digest with a business-angle note per finding) and deep-dive (narrower follow-up on one trend or paper surfaced by a prior scan). Triggers on: latest research, research trends, what's trending in, research pulse, trend scan, new ideas in, business insights, business wise, monetization ideas, market pulse, 最新研究趨勢, 研究趨勢掃描, 商業化機會, 新興想法."
metadata:
  version: "1.0.0"
  last_updated: "2026-09-08"
  status: active
  data_access_level: raw
  task_type: open-ended
  related_skills:
    - deep-research
    - grant-finder
    - academic-pipeline
---

# Research Pulse — Research Trends & Business-Insight Digest

A lightweight discovery tool — live web search plus synthesis, producing a dated, cited digest of research trends and their business/monetization angle. Not a literature-review or citation-verification tool (that's `deep-research`); this skill is for the recurring "what's new that I should know about" ask.

> **Routing discipline (v3.9.2):** see `.claude/CLAUDE.md` "Routing Discipline (v3.9.2)" for cross-skill routing rules. This skill handles trend discovery only — for rigorous literature review, source verification, or citation auditing, route to `deep-research`.

## Quick Start

**Minimal command:**
```
What's trending in AI research and academic tooling right now?
```

**Scoped to a domain:**
```
Research pulse on citation-hallucination detection — what's new, and is there a business angle?
```

**Deep dive on a prior finding:**
```
Deep-dive on the CiteCheck paper you flagged — how does it compare to our approach?
```

---

## Trigger Conditions

### Trigger Keywords

**English**: latest research, research trends, what's trending in, trend scan, research pulse, new ideas in, business insights, business wise, monetization ideas, market pulse, what's new in

**繁體中文**: 最新研究趨勢, 研究趨勢掃描, 商業化機會, 新興想法, 市場脈動

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Rigorous literature review with citation verification | `deep-research` |
| Finding a specific funding opportunity | `grant-finder` |
| Writing or revising a paper | `academic-paper` |
| Reviewing a paper | `academic-paper-reviewer` |
| Full research-to-paper pipeline | `academic-pipeline` |

---

## Mode Selection Guide

| Your Situation | Recommended Mode |
|-----------------|-------------------|
| Want a broad "catch me up" digest | `scan` |
| Want to go deeper on one trend/paper already surfaced | `deep-dive` |

---

## `scan` Mode

Run live web searches across four buckets, adapting the exact queries to whatever domain context is available (the user's stated interests, the active project, or the repo/session context if none is stated):

1. **Frontier AI/LLM & agentic-research trends** — what's shipping, what's being debated, what changed since the last scan.
2. **The user's active research domain** — if the session has an evident subject area (e.g. a repo about citation verification, a clinical specialty, a research topic under discussion), search that specifically rather than staying generic.
3. **Academic-research-tooling trends** — how AI is changing literature review, peer review, citation verification, and publishing workflows.
4. **Business / monetization trends** — pricing models, startup patterns, and commercialization angles relevant to whatever the first three buckets surfaced (e.g. if bucket 1 surfaces a new detection technique, does bucket 4 show anyone charging for it yet?).

Run 2-4 targeted searches (not one broad query) — narrow queries return more specific, dated results than one wide net.

**Output** — a Markdown digest with:
- A one-line headline per major finding, dated (cite the month/year when the source says it).
- A short "so what" line connecting the finding to the user's actual work or interests where a connection is real — never force one.
- A "Business angle" subsection only where the search evidence actually supports a commercial read (pricing model observed, funding raised, market-sizing data) — omit it rather than speculate when the evidence doesn't support it.
- A Sources list with every URL cited inline, per the suite's citation discipline (see `.claude/CLAUDE.md` "Key Rules" — all claims must have citations).

Keep the digest tight — this is a scan, not a literature review. Prefer five well-sourced findings over fifteen thin ones.

---

## `deep-dive` Mode

Takes one trend, paper, or company/product named by the user (typically from a prior `scan`) and runs additional targeted searches to answer the specific question asked — e.g. "how does this compare to our approach", "who else is working on this", "is there prior art". Same citation discipline as `scan`; no fixed output template beyond the question asked, since the point is a focused, adaptive answer rather than a repeated broad sweep.

---

## Boundaries

- This skill does not verify citations for inclusion in a paper (`deep-research` / the v3.11 `citation_existence` gate own that) — a finding surfaced here that looks relevant to the user's own citation-verification work is a pointer for them to read the source themselves, not a pre-vetted addition to the corpus.
- No schema output, no Material Passport interaction, no `academic-pipeline` handoff — this is a standalone discovery tool, same footing as `grant-finder`.
- Business-angle commentary is advisory only, grounded in what the search evidence actually shows — never invented market-sizing or revenue figures.
