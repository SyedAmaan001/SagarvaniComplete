"""Tests for the fail-closed evidence-gated release architecture (backend/release).

These double as the paper's experiments: each asserts a Section-8 scenario.
Offline, deterministic, no network or keys.
"""
from datetime import datetime, timedelta, timezone

import pytest

from release import (
    CheckOutcome, DataMode, EvidenceRecord, Gap, RecoveryAction, State, fingerprint,
    EvidenceValidator, ReleasePolicy, ReleaseContext, ReleaseEngine,
    RecoveryController, GuardedStateMachine, ProtectedArea, VesselThresholds, WarningFeed,
)
from release.experiments import (
    good_records, warning_ok, warning_on, vessel_ok, rec, TARGET, _Clock,
)

# ----------------------------------------------------------------- policy verdicts
def test_all_checks_pass_releases():
    ctx = ReleaseContext(TARGET, good_records(), warning_ok(), [], vessel_ok())
    r = ReleaseEngine().run(ctx)
    assert r.verdict == CheckOutcome.PASS
    assert r.state == State.RELEASED
    assert r.released is True


def test_active_warning_blocks():
    ctx = ReleaseContext(TARGET, good_records(), warning_on(), [], vessel_ok())
    r = ReleaseEngine().run(ctx)
    assert r.verdict == CheckOutcome.BLOCK
    assert r.state == State.BLOCKED
    assert r.released is False


def test_vessel_limit_exceeded_blocks():
    recs = [rec("wave_height_m", 3.1, "m"), rec("wind_speed_kmh", 22.0, "km/h")]
    ctx = ReleaseContext(TARGET, recs, warning_ok(), [], vessel_ok())
    r = ReleaseEngine().run(ctx)
    assert r.verdict == CheckOutcome.BLOCK
    assert r.released is False


def test_unavailable_warning_feed_is_not_evaluable_and_abstains():
    ctx = ReleaseContext(TARGET, good_records(), warning_feed=None,
                         protected_areas=[], vessel_thresholds=vessel_ok())
    r = ReleaseEngine().run(ctx)
    assert r.verdict == CheckOutcome.NOT_EVALUABLE
    assert r.state == State.ABSTAINED
    assert r.released is False


def test_not_evaluable_never_becomes_pass():
    ctx = ReleaseContext(TARGET, good_records(), warning_feed=None,
                         protected_areas=[], vessel_thresholds=vessel_ok())
    r = ReleaseEngine().run(ctx)
    assert r.verdict != CheckOutcome.PASS
    assert r.can_release is False


def test_block_takes_precedence_over_not_evaluable():
    ctx = ReleaseContext(TARGET, good_records(), warning_on(), [], vessel_thresholds=None)
    r = ReleaseEngine().run(ctx)
    assert r.verdict == CheckOutcome.BLOCK


def test_protected_area_blocks():
    areas = [ProtectedArea("Netrani", 13.36, 74.70, 5.0)]
    ctx = ReleaseContext(TARGET, good_records(), warning_ok(), areas, vessel_ok())
    r = ReleaseEngine().run(ctx)
    assert r.verdict == CheckOutcome.BLOCK


# ----------------------------------------------------------------- recovery
def test_addressable_gap_repaired_releases():
    recs = [rec("wind_speed_kmh", 22.0, "km/h")]  # wave missing
    ctx = ReleaseContext(TARGET, recs, warning_ok(), [], vessel_ok())
    r = ReleaseEngine().run(ctx, reacquire_fn=lambda a, g: good_records())
    assert r.recovery is not None and r.recovery.status == "succeeded"
    assert r.verdict == CheckOutcome.PASS
    assert r.released is True


def test_recovery_budget_exhausted_abstains():
    gaps = [Gap("MISSING_CORE_EVIDENCE", "wave", True, {"parameter": "wave_height_m"})]
    n = {"i": 0}
    def step(a, g):
        n["i"] += 1
        return [], [Gap("MISSING_CORE_EVIDENCE", "wave", True, {"c": n["i"]})]
    out = RecoveryController(budget=2).run(gaps, step)
    assert out.status == "exhausted_budget"
    assert out.cycles == 2


def test_repeated_gap_fingerprint_stops_before_budget():
    g0 = [Gap("MISSING_CORE_EVIDENCE", "wave", True, {"parameter": "wave_height_m"})]
    def step(a, g):
        return [], [Gap("MISSING_CORE_EVIDENCE", "wave", True, {"parameter": "wave_height_m"})]
    out = RecoveryController(budget=5).run(g0, step)
    assert out.status == "no_progress"
    assert out.cycles < 2


def test_deadline_exhausted_abstains():
    g0 = [Gap("MISSING_CORE_EVIDENCE", "wave", True, {"parameter": "wave_height_m"})]
    out = RecoveryController(budget=5, deadline_s=0.0, now_fn=_Clock()).run(
        g0, lambda a, g: ([], [Gap("X", "x", True, {"n": 1})]))
    assert out.status == "exhausted_deadline"


def test_unaddressable_gap_not_recovered():
    g0 = [Gap("UNIT_MISMATCH", "ft", addressable=False)]
    out = RecoveryController().run(g0, lambda a, g: ([], []))
    assert out.status == "unaddressable"


# ----------------------------------------------------------------- selector guard
def test_out_of_list_model_action_rejected():
    g0 = [Gap("MISSING_CORE_EVIDENCE", "wave", True, {"parameter": "wave_height_m"})]
    ctrl = RecoveryController(budget=3,
                             model_selector=lambda gaps, closed: "frobnicate_everything",
                             model_selector_enabled=True)
    out = ctrl.run(g0, lambda a, g: ([], []))
    first = out.trace[0]
    assert first["valid"] is False
    assert RecoveryAction(first["action"]) in set(RecoveryAction)  # rule-based, valid action


def test_valid_model_action_accepted():
    g0 = [Gap("SPATIAL_MISMATCH", "x", True, {"parameter": "wave_height_m"})]
    ctrl = RecoveryController(budget=3,
                             model_selector=lambda gaps, closed: "expand_spatial_radius",
                             model_selector_enabled=True)
    out = ctrl.run(g0, lambda a, g: ([], []))
    assert out.trace[0]["valid"] is True
    assert out.trace[0]["action"] == "expand_spatial_radius"


# ----------------------------------------------------------------- state machine guard
def test_release_without_pass_is_refused():
    sm = GuardedStateMachine()
    for s in (State.CONTEXT_VALIDATED, State.TASK_GRAPH_READY,
              State.EVIDENCE_ACQUISITION, State.EVIDENCE_VALIDATION):
        assert sm.transition(s) is True
    assert sm.transition(State.RELEASED) is False  # only from SAFETY_GATE_CHECK
    assert sm.state == State.EVIDENCE_VALIDATION


def test_released_only_reachable_from_safety_gate():
    from release.state_machine import ALLOWED
    sources = [s for s, dsts in ALLOWED.items() if State.RELEASED in dsts]
    assert sources == [State.SAFETY_GATE_CHECK]


# ----------------------------------------------------------------- audit + fingerprint
def test_audit_trace_is_complete_and_checksummed():
    ctx = ReleaseContext(TARGET, good_records(), warning_ok(), [], vessel_ok())
    r = ReleaseEngine().run(ctx)
    assert r.audit.is_complete() is True
    c = r.audit.completeness()
    assert c["n_transitions"] >= 5 and c["n_checks"] >= 4
    assert c["all_artifacts_checksummed"] is True and c["n_artifacts"] >= 2


def test_fingerprint_is_order_independent_and_stable():
    g1 = [Gap("A", attributes={"p": 1}), Gap("B", attributes={"p": 2})]
    g2 = [Gap("B", attributes={"p": 2}), Gap("A", attributes={"p": 1})]
    assert fingerprint(g1) == fingerprint(g2)
    assert fingerprint(g1) != fingerprint([Gap("A", attributes={"p": 9})])
    assert len(fingerprint(g1)) == 64  # sha-256 hex


# ----------------------------------------------------------------- evidence defects
def test_stale_evidence_detected():
    old = datetime.now(timezone.utc) - timedelta(hours=10)
    recs = [rec("wave_height_m", 1.2, "m", when=old), rec("wind_speed_kmh", 22.0, "km/h", when=old)]
    res = EvidenceValidator(target=TARGET).validate(recs)
    assert "STALE_EVIDENCE" in res.gap_codes


def test_malformed_record_detected():
    bad = EvidenceRecord(parameter="", value=1.0, unit="m", lat=13.3, lon=74.7,
                         source_id="x", data_mode=DataMode.LIVE_FORECAST)
    res = EvidenceValidator(target=TARGET).validate([bad])
    assert "MALFORMED_RECORD" in res.gap_codes


def test_unit_mismatch_detected():
    recs = [rec("wave_height_m", 1.2, "ft"), rec("wind_speed_kmh", 22.0, "km/h")]
    res = EvidenceValidator(target=TARGET).validate(recs)
    assert "UNIT_MISMATCH" in res.gap_codes


def test_out_of_range_detected():
    recs = [rec("wave_height_m", 99.0, "m"), rec("wind_speed_kmh", 22.0, "km/h")]
    res = EvidenceValidator(target=TARGET).validate(recs)
    assert "OUT_OF_RANGE" in res.gap_codes


def test_value_mismatch_detected():
    recs = [rec("wave_height_m", 1.0, "m"), rec("wave_height_m", 5.0, "m"),
            rec("wind_speed_kmh", 22.0, "km/h")]
    res = EvidenceValidator(target=TARGET).validate(recs)
    assert "VALUE_MISMATCH" in res.gap_codes
