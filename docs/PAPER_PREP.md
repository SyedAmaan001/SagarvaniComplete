# SagarVaani — Viva / Defence Preparation

Paper: *SagarVaani: Fail-Closed Evidence Gating and Bounded Recovery for Marine and Coastal Advisories.*
Authors: Syed Amaan; Mallikarjuna D M (Dayananda Sagar University). Target: IEEE CONECCT 2027.

**Status (important):** the architecture is now **implemented** (`backend/release/`, ~820 LoC) and **evaluated** (12 deterministic experiments + 85 passing tests). Defend it as an *implemented system with a behavioural, offline evaluation* — honest about what was measured (specified behaviour on deterministic fixtures) and what was not (a live-feed field study).

---

## 1. 30-second project pitch
> "Fishers decide whether to go to sea from advisories built out of many unreliable data feeds. If a feed is missing, a chatty AI can still give a confident 'it's safe' — turning a data failure into a false reassurance. SagarVaani is a release interlock that only lets an advisory out if every mandatory safety check can actually be evaluated and passes. A check whose input is missing returns a third value, `NOT_EVALUABLE`, which blocks release instead of being ignored. We implemented it as a self-contained module and ran twelve experiments that reproduce exactly the behaviour we specified — it releases only on an affirmative pass, blocks or abstains otherwise, bounds its recovery, and refuses to release without a pass — with 85 of 85 backend tests passing."

## 2. Base paper (anchor)
**C. Sun, S. Huang, D. Pompili, "LLM-Based Multi-Agent Decision-Making…," IEEE RA-L, vol. 10, 2025. DOI 10.1109/LRA.2025.3562371.** A survey of how LLM-based agents make decisions. SagarVaani's contrast: we remove the release decision *from* the agents and make it a deterministic policy with a `NOT_EVALUABLE` outcome.

## 3. Honest contribution statement
An **implemented** release-control architecture: (1) a three-valued (`PASS`/`BLOCK`/`NOT_EVALUABLE`) policy with a fixed, model-independent derivation; (2) a release interlock decoupled from the agents/LLM selector; (3) bounded closed-list recovery with gap fingerprinting + abstention; (4) a guarded state machine + checksummed audit store. Evaluated by 12 deterministic experiments and 85 tests. We claim **behavioural correctness on reference inputs**, not a field-measured safety improvement.

## 4. What is NOT novel (say this before they do)
Multi-agent decomposition, parallel retrieval, agent confidence/consensus, threshold acceptance, iterative re-execution, finite iteration caps, trace logging, marine/fisheries agents, voice input — all prior art, not claimed.

## 5. The hardest question — and a 30-second answer
**Q: "Your experiments are offline on your own fixtures and your 'official feeds' are reference inputs. How is this real evaluation and not just unit tests of your own design?"**
> "Fair challenge. The experiments are behavioural: each one feeds a constructed situation and checks the architecture produces the outcome the specification requires — pass releases, an unavailable input yields `NOT_EVALUABLE` and abstains, block takes precedence, recovery stops at its budget or when a gap fingerprint repeats, an out-of-list recovery action is rejected, and the state machine refuses a release without a pass. That is exactly the property we claim: the interlock behaves correctly and deterministically. What we do *not* claim is a field study — the warning/protected-area/vessel inputs are configurable reference inputs, and we say so in Limitations. Swapping in live official feeds is the stated next step; the same `NOT_EVALUABLE` logic already handles a feed being down."

## 6. Numbers to memorise (all in experimental_log.md)
| Number | Meaning | Source |
|---|---|---|
| **85 / 85** | full backend tests passing | E5 |
| **62 + 23** | prototype tests + new release-architecture tests | E5 |
| **12** | release-architecture experiments, all expected outcomes | E4 |
| **~820** | LoC of the release module (`backend/release/`) | E6 |
| **B = 2** | recovery cycle budget (budget exhausts at 2 cycles) | E4 |
| **1** | cycle at which a recurring fingerprint stops recovery | E4 |
| **SHA-256 / 64 hex** | artefact checksum + gap fingerprint | E4 |
| **6 / 4 / 2** | transitions / check records / checksummed artefacts in a PASS run's audit | E4 |
| **11** | Crossref-verified references | citation_verification_log.md |

## 7. ~20 likely viva questions and concise answers
1. **What problem?** Missing evidence being silently turned into an apparent "safe" advisory.
2. **What is `NOT_EVALUABLE`?** The outcome when a mandatory check's required input is unavailable; it blocks release and is never treated as pass.
3. **Different from a reject option?** Reject options abstain on *model* confidence; `NOT_EVALUABLE` abstains on *evidence availability* — no score.
4. **How is the verdict computed?** `BLOCK` if any check blocks; else `NOT_EVALUABLE` if any is unevaluable; else `PASS` iff all pass (Eq. 1). Deterministic, no LLM input.
5. **Can the LLM change the verdict?** No. The selector proposes a recovery action from a closed list; it has no write path to evidence, checks, or verdict. Experiment: an out-of-list proposal is rejected and logged.
6. **What's the fingerprint for?** No-progress detection: if the same unresolved-gap set recurs (same SHA-256), recovery stops early. Experiment: stops at cycle 1, before the budget.
7. **Closed recovery list?** retry-backoff, expand radius, extend window, switch provider, load historical (labelled), request clarification, abstain.
8. **How did you evaluate it?** 12 deterministic experiments (one per specified property) + 23 pytest assertions; full suite 85/85.
9. **Walk me through the PASS experiment.** All four mandatory checks pass (warning connected+none, clear of protected areas, within vessel limits, evidence adequate) → verdict pass → state machine enters `released`.
10. **Walk me through a NOT_EVALUABLE.** Warning feed not connected → that check is `NOT_EVALUABLE` → verdict `NOT_EVALUABLE` → the run abstains; nothing is released.
11. **Budget vs no-progress?** Budget: gaps keep changing but never resolve → stop at 2 cycles. No-progress: the same gap recurs → stop at cycle 1. Both end in abstention.
12. **How is a release without pass prevented?** The state machine's transition table makes `released` reachable only from `safety-gate-check`; a direct attempt from another state returns False (tested).
13. **What's in the audit store?** Transitions, policy-check outcomes, recovery cycles, selector invocations, and artefacts with SHA-256 checksums. A PASS run's record is complete and checksummed (6/4/2).
14. **Why is PASS reachable now when the spec said it wasn't?** We supply the three mandatory-check inputs as configurable reference inputs; when all are present and satisfied, PASS is reached. Missing any one → `NOT_EVALUABLE`.
15. **Are the official feeds real/live?** No — reference/configurable inputs. Live INCOIS/IMD/ISRO integration is future work; the `NOT_EVALUABLE` path already covers a feed being unavailable.
16. **Where's the data?** Wave/wind = Open-Meteo model forecasts; currents/PFZ/SST = archived or static reference data, labelled live/non-live.
17. **Biggest threat to validity?** External: single-region prototype, model forecasts + static layers, no live-feed field study.
18. **Any baseline comparison?** No accuracy head-to-head — the contribution is the interlock and its verified behaviour, not a new predictor.
19. **Single most novel idea?** Treating "a required safety check cannot be evaluated" as a first-class outcome that blocks release, with model-independent bounded recovery and abstention.
20. **How would you extend the evaluation?** Live feeds, coastal deployment, and injected live-source failures measuring unsupported-advisory rate vs score-based baselines.
21. **Dependencies / reproducibility?** Pure standard library, deterministic, offline; `python -m release.experiments` and `python -m pytest` reproduce everything.

## 8. Limitations (be upfront)
- Behavioural, offline evaluation on deterministic fixtures — not a field study.
- Mandatory-check inputs are reference/configurable, not live official feeds.
- Single-region prototype on model forecasts + static layers; transfer not shown.
- No accuracy comparison with another system; novelty positioning is the authors' own.

## 9. Do / Don't
- **Do** say "implemented and behaviourally evaluated"; **do** name the 12 experiments and 85 tests.
- **Do** concede openly that the feeds are reference inputs and a field study is future work.
- **Don't** claim reduced real-world accidents or a live deployment.
- **Don't** claim it outperforms any cited system — you ran no such comparison.
