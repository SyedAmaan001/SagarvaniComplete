"""Guarded state machine. Transitions are allowed only along a fixed table; the
RELEASED state is reachable only from SAFETY_GATE_CHECK. An attempted transition
not in the table is refused and recorded."""
from __future__ import annotations

from typing import Dict, List, Optional, Set

from .model import State

# Allowed transitions: from -> set of permitted next states.
ALLOWED: Dict[State, Set[State]] = {
    State.REQUESTED: {State.CONTEXT_VALIDATED, State.FAILED},
    State.CONTEXT_VALIDATED: {State.TASK_GRAPH_READY, State.FAILED},
    State.TASK_GRAPH_READY: {State.EVIDENCE_ACQUISITION, State.FAILED},
    State.EVIDENCE_ACQUISITION: {State.EVIDENCE_VALIDATION, State.FAILED, State.TIMED_OUT},
    State.EVIDENCE_VALIDATION: {State.SAFETY_GATE_CHECK, State.RECOVERY_PLANNING, State.FAILED},
    State.RECOVERY_PLANNING: {State.EVIDENCE_ACQUISITION, State.SAFETY_GATE_CHECK,
                              State.ABSTAINED, State.TIMED_OUT},
    State.SAFETY_GATE_CHECK: {State.RELEASED, State.BLOCKED, State.ABSTAINED},
    # terminal states have no outgoing transitions
    State.RELEASED: set(),
    State.ABSTAINED: set(),
    State.BLOCKED: set(),
    State.FAILED: set(),
    State.TIMED_OUT: set(),
}


class TransitionRefused(Exception):
    def __init__(self, src: State, dst: State):
        super().__init__(f"transition {src.value} -> {dst.value} is not permitted")
        self.src, self.dst = src, dst


class GuardedStateMachine:
    def __init__(self, audit=None, start: State = State.REQUESTED) -> None:
        self.state = start
        self.audit = audit
        self.history: List[State] = [start]

    def can(self, dst: State) -> bool:
        return dst in ALLOWED.get(self.state, set())

    def transition(self, dst: State, event: str = "", reason: str = "", strict: bool = False) -> bool:
        if not self.can(dst):
            if self.audit is not None:
                self.audit.record_transition(self.state.value, dst.value, event, reason, allowed=False)
            if strict:
                raise TransitionRefused(self.state, dst)
            return False
        src = self.state
        self.state = dst
        self.history.append(dst)
        if self.audit is not None:
            self.audit.record_transition(src.value, dst.value, event, reason, allowed=True)
        return True
