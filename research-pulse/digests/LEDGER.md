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
| 2026-11-23 | claude | publisher-side citation checking (Grounded AI Veracity); multi-agent debate collapse metrics; claim-to-source benchmarks; FDA/LLM-CDS (nothing new) | `2026-11-23-claude.md` | partly verified 11-26 by claude: 2609.35279 read in full; the "29 collapses / 108 corrections" freeze figure is a Figure 1 illustration, headline is 251 / 804. Silverchair deal still unconfirmed |
| 2026-11-26 | claude | existence-vs-relevance of citations (Real PMIDs, CiteAnchor); debate-ledger full read; clinical multi-agent bias (Disparity Laundering) and single-vs-multi-agent (JAMIA); AI peer-reviewer benchmark; research-tool pricing snapshot | `2026-11-26-claude.md` | arXiv items read in full text; pricing/funding from secondary guides only |

## Open follow-ups

- Funding figures still unconfirmed: Cognition ($75B, in talks) and Project Prometheus ($12B Series B). Each comes from a single aggregator. Check against primary sources. *(openai lane)*
- COMPOSER-LLM journal version (release date 2026-12-01): re-check after it is published. *(claude lane)*
- ~~Whether any major publisher has deployed a named reference-check tool.~~ Partly answered 11-23: the market is vendor-led (Grounded AI Veracity, via ScholarOne, Emerald and IOP). Still to do: confirm the Silverchair–Grounded AI deal (one aggregator source only) and the "Veracity flagged 13/65" figure against Nature 652 (2 Apr 2026). *(claude lane)*
- ~~Read arXiv 2609.35279 in full.~~ Done 11-26. Next: draft how the four-cell transition table and onset round map onto the AlSamadani Score dissent-collapse dimension, including recording which dissent was removed (see Disparity Laundering, 2610.38215). *(claude lane)*
- Run the ARS L3 anchor layer against the CiteAudit benchmark (2602.23452) before making any public precision claim. Comparator as of 11-26: CiteAnchor (2610.30355), F1 0.841 / precision 0.875; also consider CiteResolve (423 citations). *(claude lane)*
- Try the Skepthical injected-error benchmark (2611.17052, public repo) on `academic-paper-reviewer`. *(claude lane)*
- Consensus $30M round (May 2026) and current vendor pricing: confirm against primary pages. *(openai lane)*
- PAUSE-Agents: watch for a later medRxiv version. *(claude lane)*

## Sources already used

- arxiv.org/html/2607.22693v1 · arxiv.org/pdf/2607.18360 · arxiv.org/html/2607.00738v2 · arxiv.org/pdf/2607.09774 · arxiv.org/pdf/2604.26835 · arxiv.org/pdf/2602.05930
- the-decoder.com (hallucinated references at AI conferences)
- apify.com/reliable_tools/citation-checker · apify.com/wooden_scanner_c1n/reference-citation-verifier · bestdealsup.com/citely-review-n612.html · academicreviewpro.com (source-integrity 2026)
- medrxiv.org/content/10.64898/2026.07.10.26357759v1 · sciencedirect.com/science/article/pii/S2666379126004039 · arxiv.org/html/2608.26109
- health.ucsd.edu 2026-06-25 sepsis press release · par.nsf.gov/biblio/10627054 · cidrap.umn.edu (AI sepsis diagnosis)
- aifundingtracker.com 2026-11-19 · unite.ai (Cognition $75B) · blog.mean.ceo (Nov 2026 funding)
- bu.edu 2026-06-17 (Hallucinator) · library.smu.edu.sg (arXiv ban policy) · longreads.com 2026-04-06 · rubinpillay.substack.com · developmentcorporate.com (110k figure) · research.bidmc.org hallucinations.pdf
- sciflow.net press-release-grounded-ai · groundedailtd.substack.com (Silverchair, Emerald) · yespress.io/silverchair · silverchair.com/news/category/scholarone
- neurips.cc/virtual/2026/poster/139635 · arxiv.org/pdf/2609.35279 · arxiv.org/html/2605.00914v1 · caisconf.org 2026 sycophancy-collapse paper · arxiv.org/html/2601.16529v1
- arxiv.org/html/2602.23452 · arxiv.org/html/2605.27700 · arxiv.org/html/2606.13104 · ncbi PMC11419185
- arxiv.org/abs/2610.29812 · 2610.30355 · 2610.38215 · 2611.17052 · 2611.01313 · 2611.27839 · 2611.30951 · 2611.13661 · doi.org/10.1093/jamia/ocag179 · doi.org/10.2196/95400
- alpsp.org (eWorkflow–Grounded AI) · zenodo.org/records/24062771 · aclanthology.org/2026.aacl-demo.5 · wetheflywheel.com (Elicit vs Consensus vs Undermind) · theaiagentindex.com/ai-research-agents · spiritt.ai (Elicit guide)
