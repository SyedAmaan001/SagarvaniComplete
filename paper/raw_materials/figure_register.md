# Figure Register — SagarVaani IEEE paper

All figures are **original, author-drawn TikZ** embedded in `templates/ieee_conference/template.tex`. None is copied from the specification's drawings; the spec diagrams (pages 7–8) served only as conceptual source. No decorative/AI artwork is used as evidence.

| Label | Caption (short) | Type | Source / how produced | Status |
|-------|-----------------|------|-----------------------|--------|
| `fig:arch` | Fail-closed, evidence-gated release architecture | DESIGN | TikZ node/flow diagram authored from idea_sparse.md + spec; labelled "(design)" | in paper |
| `fig:flow` | Three-valued release determination and bounded allow-list recovery | DESIGN | TikZ flowchart of the release/recovery loop; references Eq. (1)–(3) | in paper |

## Tables (not figures, listed for completeness)
| Label | Caption | Type | Source |
|-------|---------|------|--------|
| `tab:status` | Implemented components of the release module (LoC) | VERIFIED | experimental_log.md E6 (backend/release/) |
| `tab:exp` | Release-architecture experiments and observed outcomes (12) | VERIFIED | experimental_log.md E4 |

## Not included (and why)
- No performance/latency plots: the evaluation is behavioural (correct-outcome) on deterministic fixtures, not a timing/accuracy study, so there are no measured curves to plot. Results are tabulated in `tab:exp` instead.
- No separate "implemented ORCA pipeline" figure: folded into prose + `tab:status` to respect the 6-page budget.
- Spec images (architecture/workflow/deployment, pages 7–8 of the specification) were **not** embedded; they are conceptual source only, and the paper's figures were redrawn independently.
