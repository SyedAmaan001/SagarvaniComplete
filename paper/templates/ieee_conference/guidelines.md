# IEEE Conference Template — Guidelines (SagarVaani)

**Target venue:** IEEE CONECCT 2027, Bangalore. **Document class:** `\documentclass[conference]{IEEEtran}`.
**Page budget:** 6 pages **including references** (double column). Confirm exact limit on the official CONECCT 2027 CFP before camera-ready.

## Structure (fixed order)
1. Abstract (≤200 words — kept tight for a 6-page paper; hard cap 250)
2. I. Introduction (ends with numbered contributions C1–C4)
3. II. Related Work
4. III. System Model and Methodology
5. IV. Implementation
6. V. Experiments and Evaluation
7. VI. Limitations and Threats to Validity
8. VII. Conclusion and Future Work
9. References

## Formatting rules
- `\documentclass[conference]{IEEEtran}`; do NOT use CVPR/ICLR/acmart.
- Figures: `\begin{figure}` with `\caption{...}` — **no figure number inside the caption text** (IEEEtran numbers it).
- Reference figures/tables as `Fig.~\ref{...}` / `Table~\ref{...}`; every float is referenced in text.
- Keep all tables and figures **before** the Conclusion where practical.
- Equations numbered; only where they add clarity and are supported by the implemented/design method.
- Bibliography via `\bibliographystyle{IEEEtran}` + `\bibliography{references}`; use only keys present in `references.bib`.
- No author/affiliation placeholders left unapproved. (Authors are confirmed: Syed Amaan; Mallikarjuna D M; Dayananda Sagar University.)

## Honesty constraints (project-specific — non-negotiable)
- The fail-closed release architecture (three-valued policy, closed-list recovery, fingerprinting, guarded state machine, checksummed audit store) is presented as **DESIGN**, not as implemented or measured.
- Experiments report ONLY: the 62-passing prototype test suite and the code-verifiable fail-closed-on-missing-data behaviour. State explicitly that architecture-level experiments were not run **because the architecture is not implemented** — never fabricate numbers to fill a table.
- No "outperforms [cite]" claims (no head-to-head experiment exists).
- Every empirical number must trace to `../../raw_materials/experimental_log.md`.
- Patents / arXiv preprints are NOT Crossref-verified; do not mix into `references.bib`. Cite patents only if CONECCT allows, in a separate list.

## Compile
- Preferred: `latexmk -pdf template.tex` or `pdflatex`×2 + `bibtex`; or Tectonic. Confirm a compiler is present before downloading one (official Tectonic releases only, with approval).
- After compiling: render every page to an image and inspect for overfull boxes, float placement, orphan headings, and page-limit compliance.
