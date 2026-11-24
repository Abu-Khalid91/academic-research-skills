# Research Pulse — Shared Ledger (Claude ⇄ OpenAI)

Several agents run research-pulse scans on this repo: Claude (Anthropic) and an OpenAI agent (ChatGPT/Codex). This file keeps them from doing the same work twice.

## Protocol (every agent, every run)

1. **Read before searching.** Read this ledger. Skip any topic marked `covered` within the last 14 days unless you have news dated after its entry. Skip any URL already listed under "Sources already used".
2. **Claim before working.** Add a row to "In progress" with your agent name and topic. If another agent's row there is under 24h old, pick a different topic.
3. **Write your digest** to `research-pulse/digests/YYYY-MM-DD-<agent>.md` (`<agent>` = `claude` or `openai`).
4. **Close out.** Move your row from "In progress" to "Run log", add your new URLs to "Sources already used", and update "Open follow-ups".
5. **Cross-check, don't repeat.** If you want to check the other agent's finding, mark it `verified` or `disputed` in its Run log row. Don't re-run its scan.

## Topic lanes (default split)

| Lane | Default owner | Notes |
|------|---------------|-------|
| Citation-integrity tooling + business angle | claude | ties to ARS v3.11 gate + feasibility study |
| Multi-agent LLMs in ICU / sepsis (AlSamadani Score) | claude | |
| Frontier AI/LLM model and agent releases | openai | |
| AI-for-science funding / startups | openai | |
| Grants (NIH etc.) | either | use `grant-finder` |

Lanes are defaults. Either agent may cover any lane after claiming it in "In progress".

## In progress

| Agent | Topic | Started (UTC) |
|-------|-------|---------------|
| — | — | — |

## Run log

| Date | Agent | Topics | Digest | Cross-check |
|------|-------|--------|--------|-------------|
| 2026-11-22 | claude | citation-hallucination detectors + pricing; multi-agent ICU; LLM sepsis trials; AI-for-science funding | `2026-11-22-claude.md` | unverified |
| 2026-11-24 | claude | AI peer review (Nov); HalluCiteChecker at AACL; sepsis multi-agent (nothing new); Nemotron for Science + week's releases; funding follow-ups | `2026-11-24-claude.md` | unverified |

## Open follow-ups

- ~~Project Prometheus $12B~~ CONFIRMED (11 Jun 2026, $41B valuation). Cognition $75B: still in talks as of 23 Nov; re-check for a close. *(openai lane)*
- GPT-6.2 Astra/Sol, Gemini 4 Neon, Qwen4-Max: aggregator-only. Confirm from primary sources. *(openai lane)*
- The 'AI review beats human review' study (Inside Higher Ed, 5 Nov): find the preprint. The host was blocked in this session. *(claude lane)*
- COMPOSER-LLM journal version (release date 2026-12-01): re-check after it is published. *(claude lane)*
- Whether any major publisher (Elsevier, Springer Nature, Wiley) has deployed a named reference-check tool. Still none found as of 2026-11-24. *(claude lane)*
- PAUSE-Agents: watch for a later medRxiv version. *(claude lane)*

## Sources already used

- arxiv.org/html/2607.22693v1 · arxiv.org/pdf/2607.18360 · arxiv.org/html/2607.00738v2 · arxiv.org/pdf/2607.09774 · arxiv.org/pdf/2604.26835 · arxiv.org/pdf/2602.05930
- the-decoder.com (hallucinated references at AI conferences)
- apify.com/reliable_tools/citation-checker · apify.com/wooden_scanner_c1n/reference-citation-verifier · bestdealsup.com/citely-review-n612.html · academicreviewpro.com (source-integrity 2026)
- medrxiv.org/content/10.64898/2026.07.10.26357759v1 · sciencedirect.com/science/article/pii/S2666379126004039 · arxiv.org/html/2608.26109
- health.ucsd.edu 2026-06-25 sepsis press release · par.nsf.gov/biblio/10627054 · cidrap.umn.edu (AI sepsis diagnosis)
- aifundingtracker.com 2026-11-19 · unite.ai (Cognition $75B) · blog.mean.ceo (Nov 2026 funding)
- aclanthology.org/2026.aacl-demo.5 · newswise.com (Georgia Tech legal citations) · aiforacademic.world (journal screening 2026) · github.com/MichaLie/journal-ai-policies
- insidehighered.com 2026-11-05 (AI review) · leiterreports.com 2026-11-03 · statmodeling.stat.columbia.edu 2026-11-09
- papers.ssrn.com 6541701 (Sepsis-Agent) · arxiv.org/pdf/2605.14723 · pubmed 42167741
- nvidianews.nvidia.com (Nemotron for Science) · hpcwire.com 2026-11-17 · trewknowledge.com 2026-11-20 · note.com/travelnatsu
- geekwire.com / axios.com (Prometheus Jun 2026) · techfundingnews.com / finance.yahoo.com (Cognition $75B) · aifundingtracker.com 2026-11-21
