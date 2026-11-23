"""Bounded, closed-list recovery controller with gap fingerprinting.

Each cycle: compute a fingerprint of the unresolved gap set; if it recurs, stop
with 'no_progress'. Otherwise a selector proposes an action; a proposal outside
the closed list is rejected and rule-based selection is used instead. The loop is
bounded by a finite cycle budget and a deadline; the selector cannot alter the
verdict (it only picks a recovery action)."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

from .model import CLOSED_RECOVERY_LIST, Gap, RecoveryAction, fingerprint


def rule_based_selector(gaps: List[Gap]) -> RecoveryAction:
    codes = {g.code for g in gaps if g.addressable}
    if not codes:
        return RecoveryAction.ABSTAIN
    if "SPATIAL_MISMATCH" in codes:
        return RecoveryAction.EXPAND_RADIUS
    if "STALE_EVIDENCE" in codes:
        return RecoveryAction.EXTEND_WINDOW
    if "MISSING_CORE_EVIDENCE" in codes or "NO_EVIDENCE" in codes:
        return RecoveryAction.RETRY_BACKOFF
    return RecoveryAction.RETRY_BACKOFF


# step_fn(action, gaps) -> (records, gaps): re-acquire + re-validate.
StepFn = Callable[[RecoveryAction, List[Gap]], Tuple[list, List[Gap]]]
# model_selector(gaps, closed_list) -> str (action name). May be out-of-list.
ModelSelector = Callable[[List[Gap], frozenset], str]


@dataclass
class RecoveryOutcome:
    status: str                       # succeeded | no_progress | exhausted_budget |
                                      # exhausted_deadline | abstained | unaddressable
    cycles: int
    final_records: list = field(default_factory=list)
    final_gaps: List[Gap] = field(default_factory=list)
    fingerprints: List[str] = field(default_factory=list)
    trace: List[dict] = field(default_factory=list)
    resolved: bool = False


class RecoveryController:
    def __init__(
        self,
        budget: int = 2,
        deadline_s: float = 30.0,
        model_selector: Optional[ModelSelector] = None,
        model_selector_enabled: bool = False,
        now_fn: Callable[[], float] = time.monotonic,
    ) -> None:
        self.budget = budget
        self.deadline_s = deadline_s
        self.model_selector = model_selector
        self.model_selector_enabled = model_selector_enabled and model_selector is not None
        self.now_fn = now_fn

    def _select(self, gaps: List[Gap], audit, cycle: int):
        """Return (action, selector_type, raw_action, valid, fallback_reason)."""
        rule_action = rule_based_selector(gaps)
        if not self.model_selector_enabled:
            return rule_action, "rules", rule_action.value, True, ""
        raw = self.model_selector(gaps, CLOSED_RECOVERY_LIST)  # may be any string
        try:
            proposed = RecoveryAction(raw)
            valid = proposed in CLOSED_RECOVERY_LIST
        except ValueError:
            proposed, valid = None, False
        if valid:
            if audit is not None:
                audit.record_selector(cycle, "model", str(raw), proposed.value, True)
            return proposed, "model", str(raw), True, ""
        fallback = f"proposal '{raw}' not in closed list; rule-based used"
        if audit is not None:
            audit.record_selector(cycle, "model", str(raw), rule_action.value, False, fallback)
        return rule_action, "model->rules", str(raw), False, fallback

    def run(self, initial_gaps: List[Gap], step_fn: StepFn, audit=None) -> RecoveryOutcome:
        if not any(g.addressable for g in initial_gaps):
            return RecoveryOutcome(status="unaddressable", cycles=0, final_gaps=initial_gaps)

        start = self.now_fn()
        cycle = 0
        seen: List[str] = []
        gaps = initial_gaps
        records: list = []
        trace: List[dict] = []

        while True:
            fp = fingerprint(gaps)
            if fp in seen:
                self._log(audit, trace, cycle, "rules", "", "", True, gaps, "no_progress")
                return RecoveryOutcome("no_progress", cycle, records, gaps, seen + [fp], trace)
            seen.append(fp)

            if self.now_fn() - start > self.deadline_s:
                self._log(audit, trace, cycle, "rules", "", "", True, gaps, "exhausted_deadline")
                return RecoveryOutcome("exhausted_deadline", cycle, records, gaps, seen, trace)
            if cycle >= self.budget:
                self._log(audit, trace, cycle, "rules", "", "", True, gaps, "exhausted_budget")
                return RecoveryOutcome("exhausted_budget", cycle, records, gaps, seen, trace)

            action, sel_type, raw, valid, fallback = self._select(gaps, audit, cycle)
            if action == RecoveryAction.ABSTAIN:
                self._log(audit, trace, cycle, sel_type, raw, action.value, valid, gaps, "abstained", fallback)
                return RecoveryOutcome("abstained", cycle, records, gaps, seen, trace)

            records, gaps = step_fn(action, gaps)
            self._log(audit, trace, cycle, sel_type, raw, action.value, valid, gaps, "applied", fallback)
            cycle += 1

            if not gaps:
                return RecoveryOutcome("succeeded", cycle, records, gaps, seen, trace, resolved=True)

    @staticmethod
    def _log(audit, trace, cycle, sel_type, raw, action, valid, gaps, outcome, fallback=""):
        gap_codes = sorted(g.code for g in gaps)
        entry = {"cycle": cycle, "selector_type": sel_type, "raw_action": raw,
                 "action": action, "valid": valid, "gap_codes": gap_codes,
                 "outcome": outcome, "fallback_reason": fallback}
        trace.append(entry)
        if audit is not None:
            audit.record_recovery_cycle(cycle, sel_type, raw, action, valid, gap_codes, outcome, fallback)
