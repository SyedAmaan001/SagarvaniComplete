# idea_sparse.md — SagarVaani

> **Framing (decided by the human author):** "Design + honest status." The paper presents the **fail-closed, evidence-gated release architecture** as a *design/specification contribution*, with the reviewed repository as a *partially-implemented prototype*. Every claim below is tagged:
> - **[VERIFIED]** — established by reading/running the reviewed repo (`SagarvaniComplete`, HEAD `40269b8`, audited 2026-11-23).
> - **[DESIGN]** — described in the SagarVaani specification/patent documents but **not** implemented in the reviewed repo.
> - **[NOT NOVEL]** — explicitly conceded as prior art by the project's own comparative analysis.

---

## Problem statement
Small-scale fishers and coastal operators rely on advisories about wave height, wind, currents and hazards drawn from heterogeneous, fallible sources (differing units, update cycles, resolutions). A generative/agentic advisory system can be fluent and confident while resting on evidence that is missing, stale, mis-located or out-of-range. In a safety setting the **absence of a warning is itself a message**: a user who receives no warning infers conditions are acceptable. A system that silently emits a best-effort advisory when evidence is missing **converts a data failure into an apparent assurance of safety**. [DESIGN-motivated, VERIFIED-relevant]

## Research gap
Known agent-orchestration controls are **score-based**: agents report confidence, agreement is measured, a score is thresholded, and the task is accepted or retried. These assess *how much agents agree*; they do **not** establish that a mandatory safety check was *capable of being evaluated at all*. A check whose input is unavailable (e.g. an official warning feed that is not connected) yields no score and is, in score-based systems, either omitted or treated as satisfied. Recovery is typically bounded only by an iteration count, and a model component may influence the release decision. [DESIGN; positioning vs base paper Sun 2025 and anchors Hendrickx 2024, Gawlikowski 2023]

## System architecture (two layers)
**(a) Reviewed prototype — "ORCA Marine Intelligence Platform" [VERIFIED]**
- 10-step pipeline (`engine/orca_pipeline.py`): Query → Interpret → Plan → Retrieve → Normalize → Reason → **Constrain (hard safety gate)** → Rank → **Verify (evidence trail)** → Respond.
- Acquisition/normalisation via `gateway/marine_data_gateway.py` (Open-Meteo marine + weather model forecasts; MOSDAC NetCDF archive; static reference registry for PFZ/SST/chlorophyll/lightning/tide).
- **Binary** hard safety/geofence gate (`engine/safety_gate.py`): `PASSED_CLEAR` / `REJECTED_UNSAFE` on MPA/firing-range geofences + per-vessel wave/wind limits + cyclone/lightning.
- **Confidence-averaging** cross-agent validator (`agents/validator.py`): `consensus = mean(agent confidences) − 0.05·(#conflicts)`.
- Evidence/provenance trail with live-vs-static labelling (`engine/evidence_engine.py`).
- Conversational layer: STT/TTS (Sarvam + browser fallback), intent-aware engine, Redis/in-memory sessions, honest `DATA_MODE`.
- FastAPI backend (`main.py`), Next.js dashboard frontend.

**(b) Target design — Fail-closed evidence-gated release architecture [DESIGN]**
- Interpreter → guarded orchestrator/state machine → planner (typed task graph) → parallel acquisition agents → evidence validator → **three-valued release policy** → **bounded closed-list recovery** → released/abstained, all with an audit store (metadata + SHA-256 artefact checksums).

## Technical method (design)
- **Evidence records** [DESIGN]: parameter, value, unit, lat/lon, source id, product id, validity interval, retrieval time, **data mode** (live-forecast / live-observation / historical-replay / test-fixture / not-available), quality flags, artefact reference, schema version. (Partial realisation [VERIFIED]: the gateway produces normalized records with provenance + live/static integrity flags, but not the full data-mode enum or per-record checksums.)
- **Validator checks** [DESIGN]: structure, units, physical range, freshness, temporal relevance, spatial coverage, evidence presence, core-evidence presence, attribution, artefact existence, value consistency, shared lineage. (Partial [VERIFIED]: range/consistency-style cross-checks exist in `validator.py`; most listed checks are not individually implemented.)

## Evidence-release policy (the core contribution — DESIGN)
Each mandatory check yields exactly one of **PASS / BLOCK / NOT_EVALUABLE**. Fixed derivation:
- **BLOCK** if any check is BLOCK;
- else **NOT_EVALUABLE** if any check is NOT_EVALUABLE;
- else **PASS** only if *every* mandatory check is PASS.
`NOT_EVALUABLE` is assigned when a check's required input is unavailable (e.g. official warning feed, protected-area geometry, expert-reviewed vessel threshold not integrated/approved). Consequences: an unavailable input can never contribute to release; adding a mandatory check can only make release harder; the policy is **deterministic** and takes no LLM/selector output as input. [DESIGN]
> **[VERIFIED] closest real analogue:** the prototype has a *single binary data-availability* fail-closed: if live wave AND wind are missing, nothing is declared safe → verdict `CANNOT_ASSESS`, gate `NOT_EVALUATED_NO_LIVE_DATA` (`orca_pipeline.py` ~L109–120, L252–256). This is **one** data-availability flag, not a policy of per-check tri-state outcomes.

## Recovery procedure (DESIGN)
On a non-PASS verdict with an *addressable* gap, a recovery controller runs in cycles: compute a **fingerprint** (SHA-256 of canonical serialisation of unresolved gap codes); if it recurs → terminate "no-progress"; else a **selector** proposes an action from a **closed list** {retry-with-backoff, expand spatial radius, extend temporal window, switch fallback provider, load historical analogue (labelled), request user clarification, abstain}. A proposal outside the list is rejected and rule-based selection is used; the selector has no write path to the verdict. Finite **cycle budget (=2)** + **deadline**; exhaustion → abstention. [DESIGN — **not implemented** in the reviewed repo.]

## Contributions (as a design paper)
1. A **three-valued release policy** (PASS/BLOCK/NOT_EVALUABLE) with a fixed, model-independent derivation rule, where NOT_EVALUABLE encodes *input unavailability* and prevents release.
2. A **deterministic release interlock** decoupled from the agents/LLM selector (selector may propose, never decide).
3. **Bounded closed-list recovery** with gap **fingerprinting** for no-progress termination, finite budget + deadline.
4. **Abstention as a terminal state** (logged reason) instead of synthesising an unsupported advisory.
5. A **guarded state machine** reaching `released` only from `safety-gate-check` on PASS, with an **audit store** (transitions, check outcomes, recovery trace, artefact checksums).
6. An **honest-data prototype** [VERIFIED] demonstrating the fail-closed-on-missing-data principle end-to-end with 62 passing tests, as partial evidence that the design's "don't assert safety without evidence" stance is implementable.

## What is NOT novel [NOT NOVEL] (conceded)
Multi-agent decomposition; parallel evidence retrieval; agent confidence/agreement/consensus; threshold-based acceptance; iterative re-execution on conflict; finite iteration limits; trace logging; applying agents to fisheries/marine/disaster info; voice input. (Per the project's comparative analysis and the base paper Sun 2025.) The paper must **not** present these as contributions.

## Implementation status (honest) [VERIFIED]
> **UPDATE 2026-11-23:** The full architecture is now **IMPLEMENTED** in `backend/release/` (~820 LoC: model, validator, policy, state_machine, recovery, audit, engine) and **evaluated** (12 deterministic experiments + 85 passing tests; see experimental_log.md E4–E6). The [DESIGN] tags above are historical; those mechanisms are now code. The bullets below describe the state *before* that implementation and are retained for provenance.
- Previously: Reviewed repo = the **ORCA/honest-data prototype**, NOT the fail-closed release architecture.
- The three-valued policy, closed-list recovery, fingerprinting, guarded transition-table state machine, and checksummed audit store are **absent** (whole-tree search for their terms returns nothing).
- The spec also records three mandatory checks (official warning, protected-area geometry, expert vessel limits) that would be fixed at NOT_EVALUABLE pending integration → **PASS not reachable** in the design's prototype either.
- Lineage-aware corroboration and numeric confidence scoring are **further embodiments**, not implemented.
- A separate repo ("Sagarvaani-Reconstructed") is said to contain the fail-closed code; it is **not available** in this checkout.

## Limitations (headline)
- No measured performance of the release architecture (it isn't implemented here) → **no** accuracy/latency/unsupported-advisory-rate numbers for it.
- Prototype data sources are partly static reference data, not live INCOIS/IMD/ISRO feeds; no verified live alert feed.
- Empirical evidence is limited to: the 62-test suite, the code-verifiable fail-closed-on-missing-data behaviour, and static code facts (see experimental_log.md).
