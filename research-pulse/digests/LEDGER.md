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
| 2026-11-22 | claude | citation-hallucination detectors + pricing; multi-agent ICU; LLM sepsis trials; AI-for-science funding | `2026-11-22-claude.md` | Cognition $75B claim disputed by 2026-11-24 run (confirmed: $48B, Sep 2026) |
| 2026-11-24 | claude | multi-agent epistemic drift/dissent collapse (AlSamadani niche); citation detection→resolution (CiteAnchor); publisher integrity deployments; integrity business angle; Cognition check; frontier releases (low confidence) | `2026-11-24-claude.md` | unverified |

## Open follow-ups

- Project Prometheus ($12B Series B) still unconfirmed. Cognition is resolved: $48B in Sep 2026, and the $75B figure is disputed. *(openai lane)*
- Frontier releases for Nov 2026 (Gemini 4 Hydrogen/Neon, GPT-6.2 Astra/Sol, Qwen4-Max) are from aggregators only. Check them against vendor announcements. *(openai lane)*
- COMPOSER-LLM journal version (release date 2026-12-01): re-check after it is published. *(claude lane)*
- Publisher tools: Springer Nature/DeepMind peer-review prototype, Nature "Veracity", and Grounded AI were seen only in search snippets. Confirm from primary sources. Elsevier and Wiley are still unknown. *(claude lane)*
- PAUSE-Agents: watch for a later medRxiv version. *(claude lane)*
- AlSamadani Score positioning: read 2610.22138 and 2611.27839 in full, and watch for any *clinical* multi-agent dissent-collapse paper. *(claude lane)*
- Re-run fetches once arxiv.org and other hosts are allowed in network settings. The Firecrawl proxy returned "invalid token" on 2026-11-24.

## Sources already used

- arxiv.org/html/2607.22693v1 · arxiv.org/pdf/2607.18360 · arxiv.org/html/2607.00738v2 · arxiv.org/pdf/2607.09774 · arxiv.org/pdf/2604.26835 · arxiv.org/pdf/2602.05930
- the-decoder.com (hallucinated references at AI conferences)
- apify.com/reliable_tools/citation-checker · apify.com/wooden_scanner_c1n/reference-citation-verifier · bestdealsup.com/citely-review-n612.html · academicreviewpro.com (source-integrity 2026)
- medrxiv.org/content/10.64898/2026.07.10.26357759v1 · sciencedirect.com/science/article/pii/S2666379126004039 · arxiv.org/html/2608.26109
- health.ucsd.edu 2026-06-25 sepsis press release · par.nsf.gov/biblio/10627054 · cidrap.umn.edu (AI sepsis diagnosis)
- aifundingtracker.com 2026-11-19 · unite.ai (Cognition $75B) · blog.mean.ceo (Nov 2026 funding)
- alphaxiv.org/abs/2610.22138 · 2611.27839 · 2610.30355 · 2610.30769 · 2611.08971 · 2610.35930 · 2610.36668 · 2611.22461 · github.com/oldwizard7/CiteANCHOR_code
- timeshighereducation.com (Springer Nature + DeepMind) · aiforacademic.world (journal screening 2026) · silverchair.com editor-ai-console · arxiv.org/pdf/2604.13940 · digital-science.com (Dimensions Citation Check API) · prnewswire (PeerTrust) · trysignalbase.com (IntegrityIQ) · techfundingnews.com (sci2sci) · wetheflywheel.com (Elicit/Consensus/Undermind) · siliconangle.com 2026-09-08 (Cognition $48B) · llmgateway.io/timeline
