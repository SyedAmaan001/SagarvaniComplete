"""Reproducible experiments for the fail-closed release architecture.

Run directly to print a results table and emit a JSON results file:

    python -m release.experiments            # from backend/
    python -m release.experiments --json out.json

Every scenario is deterministic and offline. The same scenarios are asserted as
pytest tests in tests/test_release_architecture.py.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from typing import List

from .model import (CheckOutcome, DataMode, EvidenceRecord, Gap, RecoveryAction,
                    State, fingerprint)
from .policy import (ProtectedArea, ReleaseContext, VesselThresholds, WarningFeed)
from .recovery import RecoveryController
from .engine import ReleaseEngine

TARGET = (13.35, 74.70)  # Malpe, Karnataka coast


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def rec(param, value, unit, mode=DataMode.LIVE_FORECAST, when=None, lat=13.35, lon=74.70,
        attribution="Open-Meteo", lineage=None):
    now = when or datetime.now(timezone.utc)
    return EvidenceRecord(
        parameter=param, value=value, unit=unit, lat=lat, lon=lon,
        source_id="open-meteo", product_id="marine", valid_time=_iso(now),
        retrieval_time=_iso(now), data_mode=mode, attribution=attribution,
        artifact_ref=f"{param}.json", lineage=lineage or [],
    )


def good_records() -> List[EvidenceRecord]:
    return [rec("wave_height_m", 1.2, "m"), rec("wind_speed_kmh", 22.0, "km/h")]


def warning_ok():   return WarningFeed(connected=True, active_warning=False)
def warning_on():   return WarningFeed(connected=True, active_warning=True)
def vessel_ok():    return VesselThresholds(max_wave_height_m=2.5, max_wind_speed_kmh=40.0, approved=True)


class _Clock:
    """Monotonic fake clock that advances one unit per call."""
    def __init__(self): self.t = 0.0
    def __call__(self): self.t += 1.0; return self.t


# ---------------------------------------------------------------- scenarios
def exp_pass():
    ctx = ReleaseContext(TARGET, good_records(), warning_ok(), [], vessel_ok())
    r = ReleaseEngine().run(ctx)
    return "E-PASS: all mandatory checks pass -> RELEASED", {
        "verdict": r.verdict.value, "state": r.state.value, "released": r.released,
        "expect": {"verdict": "PASS", "state": "released", "released": True},
    }


def exp_block_warning():
    ctx = ReleaseContext(TARGET, good_records(), warning_on(), [], vessel_ok())
    r = ReleaseEngine().run(ctx)
    return "E-BLOCK: active official warning -> BLOCKED", {
        "verdict": r.verdict.value, "state": r.state.value, "released": r.released,
        "expect": {"verdict": "BLOCK", "state": "blocked", "released": False},
    }


def exp_block_vessel():
    recs = [rec("wave_height_m", 3.1, "m"), rec("wind_speed_kmh", 22.0, "km/h")]
    ctx = ReleaseContext(TARGET, recs, warning_ok(), [], vessel_ok())
    r = ReleaseEngine().run(ctx)
    return "E-BLOCK2: wave exceeds vessel limit -> BLOCKED", {
        "verdict": r.verdict.value, "state": r.state.value, "released": r.released,
        "expect": {"verdict": "BLOCK", "released": False},
    }


def exp_not_evaluable():
    # warning feed not connected; evidence otherwise complete -> NOT_EVALUABLE, abstain
    ctx = ReleaseContext(TARGET, good_records(), warning_feed=None,
                         protected_areas=[], vessel_thresholds=vessel_ok())
    r = ReleaseEngine().run(ctx)
    return "E-NE: unavailable warning feed -> NOT_EVALUABLE, ABSTAINED", {
        "verdict": r.verdict.value, "state": r.state.value, "released": r.released,
        "expect": {"verdict": "NOT_EVALUABLE", "state": "abstained", "released": False},
    }


def exp_precedence():
    # one BLOCK (warning on) + one NOT_EVALUABLE (no vessel thresholds) -> BLOCK wins
    ctx = ReleaseContext(TARGET, good_records(), warning_on(), [], vessel_thresholds=None)
    r = ReleaseEngine().run(ctx)
    return "E-PREC: BLOCK + NOT_EVALUABLE -> BLOCK precedence", {
        "verdict": r.verdict.value, "released": r.released,
        "expect": {"verdict": "BLOCK", "released": False},
    }


def exp_recovery_success():
    # missing core evidence (wave) -> NOT_EVALUABLE with addressable gap; reacquire fixes it
    recs = [rec("wind_speed_kmh", 22.0, "km/h")]
    ctx = ReleaseContext(TARGET, recs, warning_ok(), [], vessel_ok())
    r = ReleaseEngine().run(ctx, reacquire_fn=lambda a, g: good_records())
    return "E-REC: addressable gap repaired by sanctioned action -> RELEASED", {
        "verdict": r.verdict.value, "state": r.state.value, "released": r.released,
        "recovery": r.recovery.status if r.recovery else None, "cycles": r.recovery.cycles if r.recovery else 0,
        "expect": {"verdict": "PASS", "released": True, "recovery": "succeeded"},
    }


def exp_recovery_budget():
    gaps = [Gap("MISSING_CORE_EVIDENCE", "wave", True, {"parameter": "wave_height_m"})]
    n = {"i": 0}
    def step(action, g):
        n["i"] += 1
        # different gap each cycle (fingerprint changes) but never resolves
        return [], [Gap("MISSING_CORE_EVIDENCE", "wave", True, {"parameter": "wave", "cycle": n["i"]})]
    out = RecoveryController(budget=2).run(gaps, step)
    return "E-BUDGET: recovery budget exhausted -> abstain", {
        "status": out.status, "cycles": out.cycles,
        "expect": {"status": "exhausted_budget", "cycles": 2},
    }


def exp_recovery_noprogress():
    g0 = [Gap("MISSING_CORE_EVIDENCE", "wave", True, {"parameter": "wave_height_m"})]
    def step(action, g):
        return [], [Gap("MISSING_CORE_EVIDENCE", "wave", True, {"parameter": "wave_height_m"})]  # identical
    out = RecoveryController(budget=2).run(g0, step)
    return "E-NOPROG: repeated gap fingerprint -> no_progress before budget", {
        "status": out.status, "cycles": out.cycles,
        "expect": {"status": "no_progress"},
    }


def exp_recovery_deadline():
    g0 = [Gap("MISSING_CORE_EVIDENCE", "wave", True, {"parameter": "wave_height_m"})]
    def step(action, g):
        return [], [Gap("X", "x", True, {"n": 1})]
    out = RecoveryController(budget=5, deadline_s=0.0, now_fn=_Clock()).run(g0, step)
    return "E-DEADLINE: deadline exceeded -> abstain", {
        "status": out.status, "expect": {"status": "exhausted_deadline"},
    }


def exp_disallowed_action():
    g0 = [Gap("MISSING_CORE_EVIDENCE", "wave", True, {"parameter": "wave_height_m"})]
    calls = {"i": 0}
    def step(action, g):
        calls["i"] += 1
        return [], []  # resolve immediately so we capture exactly one selection
    ctrl = RecoveryController(budget=3,
                             model_selector=lambda gaps, closed: "frobnicate_everything",
                             model_selector_enabled=True)
    out = ctrl.run(g0, step)
    first = out.trace[0]
    return "E-REJECT: out-of-list model proposal rejected, rule-based used", {
        "raw_action": first["raw_action"], "action": first["action"],
        "valid": first["valid"], "selector_type": first["selector_type"],
        "expect": {"valid": False, "action_in_closed_list": True},
    }


def exp_release_without_pass():
    # state machine refuses RELEASED from a non-gate state
    from .state_machine import GuardedStateMachine
    sm = GuardedStateMachine()
    sm.transition(State.CONTEXT_VALIDATED); sm.transition(State.TASK_GRAPH_READY)
    sm.transition(State.EVIDENCE_ACQUISITION); sm.transition(State.EVIDENCE_VALIDATION)
    refused = not sm.transition(State.RELEASED)  # illegal: not from safety-gate-check
    return "E-GUARD: release attempt without PASS is refused by the state machine", {
        "refused": refused, "state": sm.state.value,
        "expect": {"refused": True, "state": "evidence_validation"},
    }


def exp_audit_completeness():
    ctx = ReleaseContext(TARGET, good_records(), warning_ok(), [], vessel_ok())
    r = ReleaseEngine().run(ctx)
    c = r.audit.completeness()
    return "E-AUDIT: run produces a complete, checksummed audit record", {
        "is_complete": r.audit.is_complete(), "n_transitions": c["n_transitions"],
        "n_checks": c["n_checks"], "n_artifacts": c["n_artifacts"],
        "all_checksummed": c["all_artifacts_checksummed"],
        "expect": {"is_complete": True},
    }


SCENARIOS = [
    exp_pass, exp_block_warning, exp_block_vessel, exp_not_evaluable, exp_precedence,
    exp_recovery_success, exp_recovery_budget, exp_recovery_noprogress,
    exp_recovery_deadline, exp_disallowed_action, exp_release_without_pass,
    exp_audit_completeness,
]


def run_all():
    results = []
    for fn in SCENARIOS:
        name, data = fn()
        results.append({"experiment": name, **data})
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    results = run_all()
    print("=" * 78)
    print("SagarVaani fail-closed release architecture — experiments")
    print("=" * 78)
    for r in results:
        print(f"\n* {r['experiment']}")
        for k, v in r.items():
            if k in ("experiment", "expect"):
                continue
            print(f"    {k:16s}: {v}")
        print(f"    expect          : {r['expect']}")
    print("\n" + "-" * 78)
    print(f"{len(results)} experiments executed.")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)
        print(f"results written to {args.json}")


if __name__ == "__main__":
    main()
