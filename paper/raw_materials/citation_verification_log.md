# Citation Verification Log — SagarVaani IEEE Paper

**Verification method:** Crossref REST API, `https://api.crossref.org/works/{DOI}`.
**Verification date:** 2026-11-23.
**Policy:** Only DOIs that resolve through Crossref with matching title/author/venue/year are marked VERIFIED and are eligible for the scholarly bibliography. Patents and arXiv preprints are tracked separately and are **not** labelled Crossref-verified (per master-prompt §9).

---

## A. DOI-verified scholarly references (eligible for references.bib)

| # | DOI | Title (as in Crossref) | 1st author | Venue | Year | Type | Cites* | Crossref |
|---|-----|------------------------|-----------|-------|------|------|--------|----------|
| 1 | 10.1109/lra.2025.3562371 | LLM-Based Multi-Agent Decision-Making: Challenges and Future Directions | Sun | IEEE Robotics and Automation Letters, vol. 10 | 2025-06 | journal-article | 60 | ✅ resolves |
| 2 | 10.1007/s10994-024-06534-x | Machine learning with a reject option: a survey | Hendrickx | Machine Learning (Springer), vol. 113 | 2024-03-29 | journal-article | 134 | ✅ resolves |
| 3 | 10.1007/s10462-023-10562-9 | A survey of uncertainty in deep neural networks | Gawlikowski | Artificial Intelligence Review (Springer) | 2023-07-29 | journal-article | 1538 | ✅ resolves |

*Citation counts are Crossref `is-referenced-by-count` as of the verification date; informational only, not cited in the paper.

### Full author lists (verified from Crossref)
1. **Sun et al. 2025** — Chuanneng Sun; Songjun Huang; Dario Pompili. (3 authors)
2. **Hendrickx et al. 2024** — Kilian Hendrickx; Lorenzo Perini; Dries Van der Plas; Wannes Meert; Jesse Davis. (5 authors)
3. **Gawlikowski et al. 2023** — Jakob Gawlikowski; Cedrique Rovile Njieutcheu Tassi; Mohsin Ali; Jongseok Lee; Matthias Humt; Jianxiang Feng; … (14 authors total)

### A.2 Expansion set (verified 2026-11-23, added for Introduction + Related Work)

| # | DOI | Title | 1st author | Venue | Year | Crossref |
|---|-----|-------|-----------|-------|------|----------|
| 4 | 10.1007/s11704-024-40231-1 | A Survey on Large Language Model Based Autonomous Agents | Wang | Frontiers of Computer Science, 18(6) | 2024 | ✅ resolves |
| 5 | 10.24963/ijcai.2024/890 | Large Language Model Based Multi-agents: A Survey of Progress and Challenges | Guo | Proc. IJCAI 2024 | 2024 | ✅ resolves |
| 6 | 10.1561/2200000101 | Conformal Prediction: A Gentle Introduction | Angelopoulos | Foundations and Trends in ML, 16(4) | 2023 | ✅ resolves |
| 7 | 10.1007/s10994-021-05946-3 | Aleatoric and Epistemic Uncertainty in Machine Learning | Hüllermeier | Machine Learning, 110(3) | 2021 | ✅ resolves |
| 8 | 10.1089/big.2016.0051 | On the Safety of Machine Learning: Cyber-Physical Systems, Decision Sciences, and Data Products | Varshney | Big Data, 5(3) | 2017 | ✅ resolves |
| 9 | 10.1145/3571730 | Survey of Hallucination in Natural Language Generation | Ji | ACM Computing Surveys, 55(12) | 2023 | ✅ resolves |
| 10 | 10.1016/j.inffus.2019.12.012 | Explainable Artificial Intelligence (XAI): Concepts, Taxonomies, Opportunities and Challenges | Barredo Arrieta | Information Fusion, 58 | 2020 | ✅ resolves |
| 11 | 10.1016/j.inffus.2023.101805 | Explainable Artificial Intelligence (XAI): What We Know and What Is Left | Ali | Information Fusion, 99 | 2023 | ✅ resolves |

All eight verified by direct Crossref `works/{DOI}` lookup on 2026-11-23 with matching title/venue; long author lists use "and others" in BibTeX.

### Abstract availability
- **Sun 2025 (IEEE):** no abstract in Crossref metadata (IEEE commonly does not deposit abstracts). Abstract would need the publisher page (IEEE Xplore) — not retrieved; treat as paywalled/unavailable via Crossref.
- **Hendrickx 2024 (Springer):** no abstract in Crossref metadata. Publisher page (SpringerLink) is open-access; not yet retrieved.
- **Gawlikowski 2023 (Springer):** abstract present in Crossref (recorded in `base_paper_card.md` / related-work notes).

---

## B. Non-DOI / preprint leads — NOT Crossref-verified (kept separate; cite only if venue rules allow)

These are cited in the SagarVaani patent documents as research leads. They are **arXiv preprints or patents**, not peer-reviewed DOI-verified works. Per master-prompt §9 they must **not** be mixed into the DOI-verified bibliography and must not be labelled Crossref-verified.

| Ref | Identifier | Status | Note |
|-----|-----------|--------|------|
| VMAO | arXiv:2603.11445 | preprint, unverified | "Verified Multi-Agent Orchestration" — patent lead; peer-review status unconfirmed |
| HASSUM | arXiv:2608.14707 | preprint, unverified | "Semantic Uncertainty-Guided Orchestration…" — patent lead; peer-review status unconfirmed |
| CN122596203A, CN121581183A, CN121600667A/B, US12346832B2, CN121615675B, CN121166870A | patents | not DOI-bearing | From the Comparative Analysis prior-art study; **must not** be labelled Crossref-verified. Include only if the target venue permits patent citations, and in a clearly separate list. |

**Open item:** arXiv IDs for VMAO/HASSUM were not independently resolved in this session. If either is used in the manuscript, resolve it on arXiv and record the result here before citing.

---

## C. Citation integrity rules for the manuscript
- Every `\cite{key}` must map to an entry in this log's Section A (or an explicitly-approved Section B entry).
- Every bibliography entry must be cited at least once.
- No "SagarVaani outperforms [ref]" claim unless an actual head-to-head experiment exists (none does — see experimental_log.md).
