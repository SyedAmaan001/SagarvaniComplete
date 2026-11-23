# Base Paper Card

**Selected by the human author on 2026-11-23** as the primary positioning/comparison anchor for the SagarVaani IEEE paper. Hendrickx 2024 and Gawlikowski 2023 are retained as mandatory Related-Work anchors (separate cards not required; see citation_verification_log.md).

---

## Full citation (Crossref-verified 2026-11-23)
**C. Sun, S. Huang, and D. Pompili, "LLM-Based Multi-Agent Decision-Making: Challenges and Future Directions," *IEEE Robotics and Automation Letters*, vol. 10, no. [issue per Xplore], 2025.**
- **DOI:** 10.1109/lra.2025.3562371 → resolves (https://doi.org/10.1109/lra.2025.3562371)
- **Venue:** IEEE Robotics and Automation Letters (RA-L), vol. 10, June 2025. Peer-reviewed journal-article.
- **Authors (verified):** Chuanneng Sun; Songjun Huang; Dario Pompili.
- **Crossref citation count:** 60 (2026-11-23).

## Abstract
Not deposited in Crossref metadata (IEEE). **Not retrieved from IEEE Xplore** (treat as paywalled/unavailable in this session). Do NOT paraphrase an abstract we have not read — summary below is from the Crossref-verified title/venue and the type (survey), not from the full text.

## Type / scope
Survey / position paper on **LLM-based single- and multi-agent decision-making**. Covers how agents decide, cooperate, and communicate, and the challenges and future directions of the field.

## Dataset
N/A — survey paper; no primary dataset or benchmark of its own (to confirm against full text if accessed).

## Methodology
Literature survey + taxonomy of LLM-based decision-making (single-agent and multi-agent), synthesising mechanisms such as cooperation, communication, consensus and planning. (Detailed taxonomy to be confirmed from full text if retrieved.)

## Validation approach
Survey-level synthesis and discussion of open challenges; **no new empirical system evaluation** of its own (survey). Any specific numbers would require reading the full text — none are asserted here.

## Published numerical results
**None recorded** — we have not read the full text, so no numbers are quoted (avoids fabrication). If the paper is quoted in the manuscript, cite only claims verified from the retrieved full text.

## Strengths (for our positioning)
- IEEE venue — aligns with our IEEE conference target.
- Directly addresses the *class of system* SagarVaani sits in (multi-agent decision-making with LLMs).
- Recent (2025), well-cited, authoritative map of the field → ideal anchor for Related Work.

## Limitations (relevant to our contrast)
- It studies decision-making **by the agents**; it does not propose a release-control / abstention interlock that is independent of the agents.
- As a survey it offers no safety-release policy, no three-valued (PASS/BLOCK/NOT_EVALUABLE) outcome, and no bounded recovery mechanism.

## How SagarVaani differs (core contrast axis)
1. **Decision locus:** In the surveyed systems the *agents* (via cooperation/consensus/confidence) drive the decision. SagarVaani deliberately **removes the release decision from the agents**: a deterministic, model-independent policy derives the verdict; a learned/LLM selector may *propose* recovery actions but has **no write path** to the verdict.
2. **Three-valued release:** SagarVaani adds a `NOT_EVALUABLE` outcome for a mandatory check whose required input is unavailable — never treated as PASS. Surveyed consensus/confidence schemes have no equivalent "cannot be evaluated → withhold" primitive.
3. **Bounded, closed-list recovery with gap fingerprinting + abstention** instead of synthesising a best-effort answer.

> **Honesty note:** In the *reviewed SagarVaani repository*, items (1)–(3) are **design/specification**, not implemented code (see idea_sparse.md §Implementation status). The paper presents them as a design contribution with a partially-implemented prototype, and does NOT claim a measured improvement over Sun et al. or any cited work.
