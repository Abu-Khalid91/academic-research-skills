# AlSamadani Score: verification report

Date: 2026-11-10. This report covers what was built, what was verified, and what departs from the original brief.

## 1. Execution checks

| Check | Command | Result |
|---|---|---|
| Calculator runs | `python3 alsamadani_score_calculator.py` | Ran with zero errors in about 9 s |
| Unit tests | `python3 -m pytest -q test_alsamadani_score.py` | 38 passed |
| Manuscript build | `lualatex -interaction=nonstopmode -halt-on-error alsamadani_score_jama_manuscript.tex` (run twice) | Exit 0, **10 pages**, no overfull boxes |
| Manuscript numbers match code | `test_manuscript_macros_match_fresh_run` | Pass. Every number in the PDF is `\input` from `alsamadani_results.tex`, which the calculator generates |

## 2. Requested acceptance criteria

| Criterion | Requested | Obtained | Status |
|---|---|---|---|
| Case A (dense labs) | Tier I (≥ 80) | S = 95.7, Tier I | ✅ |
| Case B (sparse triage) | Tier III (< 50), consensus blocked | S = 38.1, Tier III, `consensus_diagnosis_index = None` | ✅ |
| Top VOI | Arterial lactate, **+6.7** | Arterial lactate, **+17.4** | ⚠️ Rank reproduced, magnitude not |
| HMAC masking | Raw MRN and unit IDs masked | Tests pass; no raw ID in any token or prompt | ✅ |
| Example tokens | `ANON-1FB9361A9FA18DBA`, `ANON-900069DE692A96FF` | Format reproduced (`ANON-` + 16 hex). These exact values cannot be reproduced without the original salt and input | ⚠️ Expected |
| Monte Carlo AUROC | **0.845** | **0.691** (95% CI 0.657 to 0.725); raw confidence 0.642 | ⚠️ Not reproduced |
| Catfish restorative effect | Shown | Dissent collapse falls and S rises, **but consensus accuracy does not improve** | ⚠️ Partly reproduced (see §4) |
| 10-page LuaLaTeX PDF | Yes | 10 pages | ✅ |

**Why the numbers differ.** All parameters (weights, half-lives, γ = 1, κ = 0.5, component weights 0.40/0.20/0.20/0.20, and the simulation settings) were fixed *before* the first run and were not changed afterward. Tuning them until the output matched 0.845 or +6.7 would have been fitting the method to a target, which a JAMA reviewer would rightly reject. The +6.7 and 0.845 figures came from the earlier Gemini draft, and its parameters are unknown. Under this score the VOI has a closed form,
`VOI_j = 100 · w_j · (lost freshness) · (α_σ + α_ρ·ρ + α_C)`. Lactate's +17.4 = 0.22 × 0.79 × 100. Reaching +6.7 would need a much smaller lactate weight or much less dissent collapse. The synthetic AUROC depends entirely on the assumed generative model, so it is not evidence of clinical discrimination in any case.

## 3. Literature anchors

Network access was limited. arXiv, PubMed, SCCM and e-hir.org could not be fetched directly, and Scite needs a paid plan. All checks below therefore rely on search-index results: publisher and venue landing pages and listings.

| Anchor in brief | Finding | Used in manuscript? |
|---|---|---|
| Wang & Yang, EMNLP 2026, "The Consistency Illusion" (CARA) | **Found.** Xiaoyang Wang & Christopher Yang, EMNLP 2026 Main, arXiv:2606.08457. Debate lowers contradiction while reasoning-chain similarity falls; benchmarks MedQA-USMLE and MedThink-Bench | Yes |
| AgentRx (May 2026), arXiv:2605.10286 | **Found.** Al Jorf & Shamout. Single-agent beat naive multi-agent; both trailed supervised fusion; MIMIC ICU data. The claim that multi-agent was **"worse calibrated"** appears only in a secondary listing, and one aggregator even contradicts the main finding | Yes, accuracy finding only. Calibration claim omitted |
| Early Sepsis MAS (Apr 2026), 30% hallucination | **Found, but different from the brief.** Iapascurta et al., *Healthc Inform Res* 2026;32(2):190–195, doi:10.4258/hir.2026.32.2.190. 3-agent RAG system; hallucinations in **3 of 10 cases**; reviewed by 2 intensivists. **Not confirmed:** MIMIC-IV use, a T = 0 h setting, or a "missing labs" design | Yes, stated as 3 of 10 cases |
| HARN (Oct 2026), 4-agent MIMIC-IV, 50 physicians | **Not found** in 2 targeted searches. The closest verified work is MIRA, "Towards autonomous medical AI agents", *Nature* 2026 (>500 MIMIC-IV ED cases) | HARN omitted; MIRA cited (author list still to verify) |
| J Med Syst (Sep 2026), 91% stochastic errors (via Bioengineer.org) | **Not found** in 2 targeted searches. Bioengineer.org is a news aggregator, not a primary source | Omitted |
| SSC 2026 guidelines | **Found.** *Crit Care Med* 2026, doi:10.1097/CCM.0000000000007075; *Intensive Care Med* doi:10.1007/s00134-026-08361-1; lead author per EMCrit: H. Prescott. MAP initial target 65 (60–65 at age ≥ 65), norepinephrine first line, antimicrobials ideally within 1 h, balanced crystalloids. **The 30 mL/kg statement's 2026 wording and strength were not confirmed** | Yes, with verification flags in the code |
| Saudi "AI Principles in Media" | **Found** (Ministry of Media with SDAIA and partners; 8 principles, including disclosure and human responsibility). **Principle numbering (1 and 5) and the issue date were not confirmed** | Yes, without principle numbers |
| "JAMA Network (2026)" AI guidance | Cited the verified Flanagin et al., *JAMA* 2024;331(13):1096-1098. No 2026 update was found | Yes (2024) |

Well-established references (Sepsis-3, SOFA, MIMIC-IV, eICU, TRIPOD+AI, KDIGO 2012, Guo 2017, Lin 1991, Goddard 2012, Wong 2021) were cited from prior knowledge with their standard DOIs. **Run every reference through a DOI resolver before submission.**

## 4. Substantive finding to know before submitting

In the scaling benchmark, a stubborn "catfish" agent keeps dissent collapse low **by construction**. It raises S by up to about 25 points with no gain in accuracy (all accuracy differences ≤ 1.0 percentage point). The ρ term can therefore be gamed. The manuscript reports this openly and proposes fixes: require evidence-grounded dissent, exclude designated dissenters from D_r, or cap the credit the dissent term can contribute. Reviewers will find this weakness anyway, so it is better reported by the author.

## 5. Claims softened from the brief

- "TRIPOD+AI compliant" became "reported with reference to TRIPOD+AI" plus a status eTable. Most items cannot be met without real data.
- "Complies with FDA §3060(a) non-device CDS" became "designed with reference to the criteria; no regulatory determination". Time-critical ICU software can fall *outside* the non-device criteria.
- "100% bedside utility" became "guideline **coverage** by construction" (the engine always returns at least 1 recommendation), which is not evidence of efficacy.
- AI disclosure: the manuscript states that Gemini and Claude were used, and it carries a bracketed line the author must confirm.

## 6. Author to-do before submission

1. Fill in the Conflict of Interest and Funding sections, and confirm the AI disclosure.
2. Complete the author lists for MIRA and SSC 2026, and verify every DOI.
3. Read the SSC 2026 primary text and adjust the rule-engine wording, especially the 30 mL/kg statement.
4. Verify the MIMIC-IV/eICU item IDs against your local dictionaries.
5. JAMA Internal Medicine's Original Investigation format expects about 3000 words and double spacing for submission. A methods and simulation paper may fit a Research Letter or Special Communication better, or a preprint first.
6. MIMIC-IV/eICU DUA: do not send credentialed data to third-party LLM APIs unless PhysioNet's responsible-use guidance permits it.
