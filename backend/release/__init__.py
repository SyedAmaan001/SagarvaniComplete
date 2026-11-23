"""SagarVaani fail-closed evidence-gated release architecture.

A deterministic release-control layer that sits above the multi-agent acquisition
system. Public API:

    from release import ReleaseEngine, ReleaseContext, build_warning_feed, ...

Components:
  model.py          evidence records, data modes, three-valued outcomes, fingerprint
  validator.py      rule checks over evidence -> gaps
  policy.py         mandatory release checks + three-valued derivation (PASS/BLOCK/NOT_EVALUABLE)
  state_machine.py  guarded state machine (transition table; RELEASED only from SAFETY_GATE_CHECK)
  recovery.py       closed-list recovery, gap fingerprinting, budget + deadline, no-progress stop
  audit.py          checksummed audit store
  engine.py         orchestrates the above; release only on an affirmative PASS
"""
from .model import (
    DataMode, CheckOutcome, Verdict, State, RecoveryAction, CLOSED_RECOVERY_LIST,
    EvidenceRecord, Gap, fingerprint,
)
from .validator import EvidenceValidator, ValidationResult
from .policy import ReleasePolicy, ReleaseContext, PolicyResult, WarningFeed, ProtectedArea, VesselThresholds
from .state_machine import GuardedStateMachine, TransitionRefused
from .recovery import RecoveryController, RecoveryOutcome
from .audit import AuditStore
from .engine import ReleaseEngine, ReleaseResult

__all__ = [
    "DataMode", "CheckOutcome", "Verdict", "State", "RecoveryAction", "CLOSED_RECOVERY_LIST",
    "EvidenceRecord", "Gap", "fingerprint",
    "EvidenceValidator", "ValidationResult",
    "ReleasePolicy", "ReleaseContext", "PolicyResult", "WarningFeed", "ProtectedArea", "VesselThresholds",
    "GuardedStateMachine", "TransitionRefused",
    "RecoveryController", "RecoveryOutcome",
    "AuditStore",
    "ReleaseEngine", "ReleaseResult",
]
