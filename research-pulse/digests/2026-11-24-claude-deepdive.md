# Research Pulse — 2026-11-24 (deep-dive): AI vs human peer review

This follows up item 1 of `2026-11-24-claude.md`. The session's network blocks gking.harvard.edu and arxiv.org, and the Firecrawl connector returned "Invalid token". Everything below therefore comes from search-result abstracts, listings and secondary coverage, not from reading the full papers. Read both papers yourself before relying on any number.

## A. King & Worthington (Harvard IQSS, Oct 2026): "AI Article Reviews Dominate Human Peer Reviews at Their Best"
- **Data:** 134 human reviews of 124 papers (2019–2026) from rapidPeer, a Harvard service that pays expert reviewers to give feedback before a paper is submitted to a journal. Each human review was matched with a review written by Claude Opus.
- **Results:**
  - An AI judge preferred the AI review in every decided pair (132/132).
  - Human editors preferred it about 87% of the time. One account puts this at 3 former editors × 10 pairs = 30 judgments, 26 of them for the AI review. That is a small sample.
  - **Error rate:** 5.5% of the AI reviews' claims about the manuscript were judged incorrect, against 15.9% for the human reviews.
  - In a replication using two model families, a new prompt and a new rubric, the AI review was preferred 97.1% of the time by an Opus judge and 94.2% by a GPT judge.
- **Critiques:**
  - Bagrow (27 Oct) argues the evidence mostly shows that AI judges prefer AI reviews, and that rapidPeer's instructions make "humans at their best" an unproven framing.
  - All the AI reviews in the main study came from a single model family.
  - The AI reviews were never delivered to the authors, so nothing measures their effect on how papers get revised.
- **Status:** not yet peer reviewed. One source says it appeared in Nature Machine Intelligence, but that conflicts with all other coverage, so treat it as unverified. I could not read the authors' policy recommendations, including the "author dossier" idea from Inside Higher Ed.

## B. ICML 2026 randomized policy experiment (arXiv 2609.19420)
- **Design:** 24,661 papers and 17,886 reviewers. Each reviewer was randomly assigned either a ban on LLM use or permission for limited use.
- **Result:** the policy assignment had no detectable effect on scores, reviewer confidence or acceptance decisions. Reviews under the permissive policy were about 5.5–7% longer.
- **Compliance (survey, n=1,486):** 22.5% of reviewers under the ban used an LLM anyway. 36.5% of reviewers under the permissive policy made at least one use the policy did not allow.
- Kim's own page says the paper won a best-paper award at the NeurIPS 2026 AI-Native Academia workshop. I have not confirmed this.

## What this means for ARS
1. **Agreement between an AI judge and an AI reviewer is weak evidence.** Paper A's own gap (100% with the AI judge, 87% with a small human panel) is the judge-bias problem the ARS v3.12 same-family calibration note warns about. When `academic-paper-reviewer` runs in calibration mode, human ground truth should be required rather than optional.
2. **Count factual errors, not preference.** The 5.5% vs 15.9% wrong-claims figure is the most defensible result in paper A. A per-review error rate (claims about the manuscript that turn out false) would be a useful calibration metric for the ARS reviewer. It fits the existing Three-Layer Citation Emission anchors, because each review claim could point to a quote or page.
3. **Rules do not stop undisclosed AI use.** About a quarter to a third of ICML reviewers broke their assigned policy. That supports making disclosure mode and audit trails the product, instead of relying on bans.

## Business angle
- **What the evidence shows:** rapidPeer is a paid service that provides expert review before journal submission. Paper A is in effect a benchmark showing that an AI review can match or beat that paid product on quality and on wrong claims. I found no public price for rapidPeer.
- **Opportunity (my inference, not demonstrated):** an AI review that is anchored to the manuscript, reports its error rate and is ready to disclose, sold to authors before submission or to editors at triage. Paper B suggests venues will not be able to enforce bans, which favors tools that are disclosure-first.
- **Risk:** AI review before submission is becoming cheap. As with citation checking, the margin is likely in audited, calibrated workflows rather than in generating the review itself.

## Sources
- https://gking.harvard.edu/files/peerless.pdf
- https://gking.harvard.edu/peerless/
- https://bagrow.com/blog/2026/10/27/peerless/
- https://entropyclinic.substack.com/p/ai-reviews-beat-humansat-what-level
- https://nicolaijfoss.substack.com/p/when-ai-becomes-the-better-referee
- https://www.timeshighereducation.com/news/ai-article-review-better-humans-their-best
- https://fourweekmba.com/ai-editors-preferred-claudes-paper-reviews-in-87-of-picks/
- https://cspaper.org/articles/ai-vs-human-peer-review
- https://arxiv.org/abs/2609.19420
- https://neurips.cc/virtual/2026/loc/atlanta/166267
- https://sunniesuhyoung.github.io/
- https://arxiv.org/pdf/2605.03202 (related: "Stop Automating Peer Review Without Rigorous Evaluation")

This is a discovery deep-dive. Nothing here is checked for citation in a paper; use deep-research for that.
