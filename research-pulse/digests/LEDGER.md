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
| 2026-11-28 | claude | AI-reviewer benchmark (enforced retrieval, 2611.17052); Lancet 98.4% no-action + retroactive screening; AI peer review adoption + Google Deep Review; agent-authored research (JAR, YouRA); ICU/sepsis (nothing new) | `2026-11-28-claude.md` | unverified (arxiv/IHE/casrai not fetchable; 2611.17052 read via alphaXiv) |
| 2026-11-23 | claude | publisher-side citation checking (Grounded AI Veracity); multi-agent debate collapse metrics; claim-to-source benchmarks; FDA/LLM-CDS (nothing new) | `2026-11-23-claude.md` | unverified (arxiv/substack not fetchable this run) |

## Open follow-ups

- Funding figures still unconfirmed: Cognition ($75B, in talks) and Project Prometheus ($12B Series B). Each comes from a single aggregator. Check against primary sources. *(openai lane)*
- COMPOSER-LLM journal version (release date 2026-12-01): re-check after it is published. *(claude lane)*
- ~~Whether any major publisher has deployed a named reference-check tool.~~ Partly answered 11-23: the market is vendor-led (Grounded AI Veracity, via ScholarOne, Emerald and IOP). Still to do: confirm the Silverchair–Grounded AI deal (11-28: NOT on Silverchair's own ScholarOne news page; only Grounded AI's Substack) and the "Veracity flagged 13/65" figure against Nature 652 (2 Apr 2026). *(claude lane)*
- Read arXiv 2609.35279 (debate collapse/correction ledger) in full. It is a candidate method to borrow for the AlSamadani Score dissent-collapse dimension. *(claude lane)*
- Run the ARS L3 anchor layer against the CiteAudit benchmark (2602.23452) before making any public precision claim. *(claude lane)*
- PAUSE-Agents: watch for a later medRxiv version. *(claude lane)*
- Add arXiv 2611.17052 (AI-reviewer error-injection benchmark; released eval set) as a second external benchmark for the ARS L3 anchor layer. Prioritise its astrophysics citation subset, where model memory is weak. *(claude lane)*
- Look into a retroactive back-catalogue screening product. The Lancet audit found no publisher action on 98.4% of affected papers, and PLOS is exploring system-wide screening. Find out whether any vendor prices this. *(claude lane)*
- Verify the 'Journal of Agent Research' (launched 4 Nov 2026?) and ETRI YouRA claims against primary sources. *(openai lane)*

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
- alphaxiv.org/abs/2611.17052 · casrai.org (AI-reviewer benchmark) · neurips.cc/virtual/2026/poster/152885 · arxiv.org/abs/2611.21950v1 · arxiv.org/pdf/2605.23320 · alphaxiv.org society-ai-scientists
- retractionwatch.com 2026-05-07 (1 in 277) · uef.fi (Lancet audit) · healthday.com · scicampus.com · blog.pebblous.ai 2026-11 · silverchair.com relay-integrations
- insidehighered.com 2026-11-05 · phys.org 2026-11-ai-peer · pubsonline.informs.org mnsc.2026.00184 · academiainsider.com · buildmvpfast.com · digitaltoday.co.kr (YouRA) · communities.springernature.com (COMPOSER-LLM)
