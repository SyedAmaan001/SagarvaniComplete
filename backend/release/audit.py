"""Checksummed audit store. Records state transitions, policy-check outcomes,
recovery cycles, selector invocations, and raw artefacts with SHA-256 checksums."""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List


class AuditStore:
    def __init__(self) -> None:
        self.transitions: List[Dict[str, Any]] = []
        self.checks: List[Dict[str, Any]] = []
        self.recovery_cycles: List[Dict[str, Any]] = []
        self.selector_invocations: List[Dict[str, Any]] = []
        self.artifacts: List[Dict[str, Any]] = []
        self.events: List[Dict[str, Any]] = []

    # --- recorders --------------------------------------------------------
    def record_transition(self, src: str, dst: str, event: str, reason: str, allowed: bool) -> None:
        self.transitions.append(
            {"from": src, "to": dst, "event": event, "reason": reason, "allowed": allowed}
        )

    def record_checks(self, verdict: str, checks) -> None:
        for name, outcome, detail in checks:
            self.checks.append({"check": name, "outcome": getattr(outcome, "value", str(outcome)),
                                "detail": detail, "verdict": verdict})

    def record_recovery_cycle(self, cycle: int, selector_type: str, raw_action: str,
                              action: str, valid: bool, gap_codes, outcome: str,
                              fallback_reason: str = "") -> None:
        self.recovery_cycles.append(
            {"cycle": cycle, "selector_type": selector_type, "raw_action": raw_action,
             "action": action, "valid": valid, "gap_codes": list(gap_codes),
             "outcome": outcome, "fallback_reason": fallback_reason}
        )

    def record_selector(self, cycle: int, selector_type: str, raw_action: str,
                        validated_action: str, valid: bool, fallback_reason: str = "") -> None:
        self.selector_invocations.append(
            {"cycle": cycle, "selector_type": selector_type, "raw_action": raw_action,
             "validated_action": validated_action, "valid": valid, "fallback_reason": fallback_reason}
        )

    def record_artifact(self, name: str, data: bytes) -> str:
        checksum = hashlib.sha256(data).hexdigest()
        self.artifacts.append({"name": name, "size": len(data), "sha256": checksum})
        return checksum

    def event(self, kind: str, **fields: Any) -> None:
        self.events.append({"kind": kind, **fields})

    # --- queries ----------------------------------------------------------
    def completeness(self) -> Dict[str, Any]:
        """Did the run produce a complete, inspectable record?"""
        return {
            "has_transitions": len(self.transitions) > 0,
            "has_checks": len(self.checks) > 0,
            "all_artifacts_checksummed": all(a.get("sha256") for a in self.artifacts),
            "n_transitions": len(self.transitions),
            "n_checks": len(self.checks),
            "n_recovery_cycles": len(self.recovery_cycles),
            "n_artifacts": len(self.artifacts),
        }

    def is_complete(self) -> bool:
        c = self.completeness()
        return c["has_transitions"] and c["has_checks"] and c["all_artifacts_checksummed"]
