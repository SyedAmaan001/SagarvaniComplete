"""Release engine: drives the guarded state machine through validation, the
three-valued policy, bounded recovery, and (only on an affirmative PASS) release."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from typing import Callable, List, Optional

from .audit import AuditStore
from .model import CheckOutcome, Gap, RecoveryAction, State
from .policy import ReleaseContext, ReleasePolicy, PolicyResult
from .recovery import RecoveryController, RecoveryOutcome
from .state_machine import GuardedStateMachine
from .validator import EvidenceValidator, ValidationResult

# reacquire_fn(action, gaps) -> new list[EvidenceRecord]
ReacquireFn = Callable[[RecoveryAction, List[Gap]], list]


@dataclass
class ReleaseResult:
    verdict: CheckOutcome
    state: State
    can_release: bool
    policy: PolicyResult
    validation: ValidationResult
    audit: AuditStore
    recovery: Optional[RecoveryOutcome] = None

    @property
    def released(self) -> bool:
        return self.state == State.RELEASED and self.can_release


class ReleaseEngine:
    def __init__(
        self,
        validator: Optional[EvidenceValidator] = None,
        policy: Optional[ReleasePolicy] = None,
        recovery: Optional[RecoveryController] = None,
    ) -> None:
        self.policy = policy or ReleasePolicy()
        self.recovery = recovery or RecoveryController()
        self._validator_factory = (lambda: validator) if validator is not None else None

    def _validator(self, ctx: ReleaseContext) -> EvidenceValidator:
        if self._validator_factory is not None:
            return self._validator_factory()
        return EvidenceValidator(target=ctx.target)

    def run(self, ctx: ReleaseContext, reacquire_fn: Optional[ReacquireFn] = None) -> ReleaseResult:
        audit = AuditStore()
        sm = GuardedStateMachine(audit)
        sm.transition(State.CONTEXT_VALIDATED, "context_ok")
        sm.transition(State.TASK_GRAPH_READY, "planned")
        sm.transition(State.EVIDENCE_ACQUISITION, "acquire")
        self._checksum_records(ctx.records, audit)
        sm.transition(State.EVIDENCE_VALIDATION, "validate")

        validator = self._validator(ctx)
        validation = validator.validate(ctx.records)
        policy_res = self.policy.evaluate(ctx, validation)
        audit.record_checks(policy_res.verdict.value, policy_res.checks)

        if policy_res.verdict == CheckOutcome.PASS:
            return self._gate(sm, policy_res, validation, audit, None)

        if policy_res.verdict == CheckOutcome.BLOCK:
            sm.transition(State.SAFETY_GATE_CHECK, "gate")
            sm.transition(State.BLOCKED, "blocked")
            return ReleaseResult(policy_res.verdict, sm.state, False, policy_res, validation, audit)

        # NOT_EVALUABLE
        if validation.has_addressable_gap() and reacquire_fn is not None:
            sm.transition(State.RECOVERY_PLANNING, "recover")
            state = {"validation": validation, "policy": policy_res, "ctx": ctx}

            def step_fn(action: RecoveryAction, gaps: List[Gap]):
                new_records = reacquire_fn(action, gaps)
                self._checksum_records(new_records, audit)
                v = validator.validate(new_records)
                c = replace(state["ctx"], records=new_records)
                p = self.policy.evaluate(c, v)
                audit.record_checks(p.verdict.value, p.checks)
                state.update(validation=v, policy=p, ctx=c)
                remaining = [] if p.verdict == CheckOutcome.PASS else v.gaps
                return new_records, remaining

            outcome = self.recovery.run(validation.gaps, step_fn, audit)
            policy_res = state["policy"]
            validation = state["validation"]
            if outcome.resolved and policy_res.verdict == CheckOutcome.PASS:
                return self._gate(sm, policy_res, validation, audit, outcome)
            sm.transition(State.ABSTAINED, f"recovery_{outcome.status}")
            return ReleaseResult(policy_res.verdict, sm.state, False, policy_res, validation, audit, outcome)

        # NOT_EVALUABLE with no addressable gap (e.g. missing integrated input) -> abstain
        sm.transition(State.RECOVERY_PLANNING, "recover")
        sm.transition(State.ABSTAINED, "no_addressable_gap")
        return ReleaseResult(policy_res.verdict, sm.state, False, policy_res, validation, audit)

    def _gate(self, sm: GuardedStateMachine, policy_res: PolicyResult,
              validation: ValidationResult, audit: AuditStore,
              recovery: Optional[RecoveryOutcome]) -> ReleaseResult:
        sm.transition(State.SAFETY_GATE_CHECK, "gate")
        # Guard: the released state is entered only on an affirmative PASS.
        if policy_res.verdict == CheckOutcome.PASS:
            sm.transition(State.RELEASED, "released")
        else:
            sm.transition(State.ABSTAINED, "not_pass_at_gate")
        can = sm.state == State.RELEASED and policy_res.verdict == CheckOutcome.PASS
        return ReleaseResult(policy_res.verdict, sm.state, can, policy_res, validation, audit, recovery)

    @staticmethod
    def _checksum_records(records, audit: AuditStore) -> None:
        for i, rec in enumerate(records):
            blob = json.dumps(asdict(rec), default=str, sort_keys=True).encode("utf-8")
            audit.record_artifact(f"{rec.parameter}:{i}", blob)
