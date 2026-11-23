# experimental_log.md — SagarVaani

**Authoritative record for every empirical number used in the paper.** No number enters the manuscript unless it has an entry here. Fabrication is prohibited.

> **Scope change (2026-11-23):** The fail-closed release architecture has now been **implemented** (`backend/release/`) and **evaluated**. The earlier "design-only / cannot produce" status is superseded. All Section-8 experiments now run and pass with the expected outcomes.

**Environment (common to all entries):**
- Repo: `SagarvaniComplete`, branch `main`. New code: `backend/release/` package + `backend/tests/test_release_architecture.py`.
- OS: Windows 11 (10.0.26200). Python **3.13.6** (`backend/venv`).
- Date: **2026-11-23**. No network, no API keys, no paid APIs, no production endpoints. All experiments deterministic and offline.

---

## PART 1 — Test suites

### E5 — Full backend test suite passes (post-implementation)
- **Value:** **85 of 85 tests passed, 0 failed** (21 cosmetic FastAPI deprecation warnings).
- **Breakdown:** 62 prototype tests (unchanged) + **23 new release-architecture tests**.
- **Command:** `python -m pytest -q` (from `backend/`).
- **Raw output:** `raw_outputs/E5_pytest_full.txt` (`85 passed, 21 warnings`).
- **Type:** measured (test runner). **Runtime:** ~7.5 s (environment-dependent; not a performance claim).

### E1/E2 — Prototype suite (unchanged, retained)
- 62 prototype tests across conversation (23), voice (13), health/config (14), sessions/pipeline (10), full-voice-flow (2). Raw: `raw_outputs/E1_pytest_run.txt`, `E2_test_inventory.txt`.

---

## PART 2 — Release-architecture experiments (the core results)

### E4 — Twelve release-control experiments, all with expected outcomes
- **Runner:** `python -m release.experiments --json <out>` (from `backend/`).
- **Raw output:** `raw_outputs/E4_release_experiments.json` (12 records). Also asserted as pytest tests (E5).
- **Type:** measured/observed from executing the implemented code. Each row below is the actual observed result.

| # | Experiment | Observed result |
|---|-----------|-----------------|
| 1 | All mandatory checks pass | verdict **PASS** → state **released** |
| 2 | Active official warning | verdict **BLOCK** → state **blocked**, no release |
| 3 | Wave exceeds vessel limit | verdict **BLOCK**, no release |
| 4 | Unavailable warning feed | verdict **NOT_EVALUABLE** → state **abstained**, no release |
| 5 | BLOCK + NOT_EVALUABLE together | verdict **BLOCK** (precedence) |
| 6 | Protected-area intersection | verdict **BLOCK** |
| 7 | Addressable gap repaired by sanctioned action | recovery **succeeded** in **1 cycle** → verdict **PASS** → **released** |
| 8 | Recovery budget exhausted | status **exhausted_budget** at **2 cycles** → abstain |
| 9 | Repeated unresolved-gap fingerprint | status **no_progress** at **cycle 1** (before budget) → abstain |
| 10 | Recovery deadline exceeded | status **exhausted_deadline** → abstain |
| 11 | Out-of-list model recovery proposal | **rejected** (valid=False); rule-based action used instead and logged |
| 12 | Release attempt without PASS | state machine **refuses** the transition (stays in `evidence_validation`) |
| 13 | Audit completeness (on a PASS run) | audit **complete**: 6 transitions, 4 check records, 2 checksummed artefacts |

(Items 1–13 above correspond to 12 scenario functions; protected-area and the two block cases are listed separately for the table.)

### Supporting measured facts
- **Gap fingerprint** = SHA-256 of a canonical serialisation of the unresolved gap set; **64 hex chars**; order-independent (verified in `test_fingerprint_is_order_independent_and_stable`).
- **Recovery cycle budget** B = 2 (default); **deadline** configurable.
- **Evidence-defect detection** (validator): STALE_EVIDENCE, MALFORMED_RECORD, UNIT_MISMATCH, OUT_OF_RANGE, VALUE_MISMATCH each detected (dedicated tests).

### E6 — Implementation size
- **Release package core ≈ 820 LoC** (model 116, validator 196, policy 138, state_machine 56, recovery 128, audit 68, engine 118) + experiment runner 237. **Counted** (`wc -l`).
- Existing backend prototype ≈ 8.3k LoC (≈8354; rounded **≈8.3k** in the paper).

---

## PART 3 — Honesty notes (what the results do and do NOT claim)
- The experiments establish that the **mechanisms behave as specified** (three-valued derivation, precedence, bounded recovery, fingerprint no-progress, selector rejection, guarded release, audit completeness). They are **functional/behavioural** results on deterministic fixtures.
- They are **NOT** a field study: no claim of reduced real-world accidents, no live-feed deployment, no human-subject evaluation. Inputs (warning feed, protected areas, vessel thresholds) use **reference/configurable** data, not live official feeds — stated in Limitations.
- No head-to-head accuracy comparison with another system is claimed (none was run); the contribution is the architecture and its verified behaviour.
