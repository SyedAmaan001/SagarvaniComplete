"""Core data model for the fail-closed release architecture."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DataMode(str, Enum):
    """How an evidence value was obtained. A non-live record never satisfies a
    check that requires live evidence."""
    LIVE_FORECAST = "live_forecast"
    LIVE_OBSERVATION = "live_observation"
    HISTORICAL_REPLAY = "historical_replay"
    TEST_FIXTURE = "test_fixture"
    NOT_AVAILABLE = "not_available"


LIVE_MODES = frozenset({DataMode.LIVE_FORECAST, DataMode.LIVE_OBSERVATION})


class CheckOutcome(str, Enum):
    """Three-valued outcome of a mandatory release check (and the overall verdict)."""
    PASS = "PASS"
    BLOCK = "BLOCK"
    NOT_EVALUABLE = "NOT_EVALUABLE"


# The overall verdict ranges over the same three values.
Verdict = CheckOutcome


class State(str, Enum):
    REQUESTED = "requested"
    CONTEXT_VALIDATED = "context_validated"
    TASK_GRAPH_READY = "task_graph_ready"
    EVIDENCE_ACQUISITION = "evidence_acquisition"
    EVIDENCE_VALIDATION = "evidence_validation"
    RECOVERY_PLANNING = "recovery_planning"
    SAFETY_GATE_CHECK = "safety_gate_check"
    RELEASED = "released"
    ABSTAINED = "abstained"
    BLOCKED = "blocked"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


TERMINAL_STATES = frozenset({
    State.RELEASED, State.ABSTAINED, State.BLOCKED, State.FAILED, State.TIMED_OUT,
})


class RecoveryAction(str, Enum):
    """The closed list of permitted recovery actions."""
    RETRY_BACKOFF = "retry_with_backoff"
    EXPAND_RADIUS = "expand_spatial_radius"
    EXTEND_WINDOW = "extend_temporal_window"
    SWITCH_PROVIDER = "switch_fallback_provider"
    LOAD_HISTORICAL = "load_historical_analogue"
    REQUEST_CLARIFICATION = "request_clarification"
    ABSTAIN = "abstain"


CLOSED_RECOVERY_LIST = frozenset(RecoveryAction)


@dataclass
class EvidenceRecord:
    parameter: str
    value: Optional[float]
    unit: str
    lat: float
    lon: float
    source_id: str
    product_id: str = ""
    obs_time: Optional[str] = None
    issue_time: Optional[str] = None
    valid_time: Optional[str] = None
    retrieval_time: Optional[str] = None
    data_mode: DataMode = DataMode.NOT_AVAILABLE
    quality_flags: List[str] = field(default_factory=list)
    source_uri: str = ""
    attribution: str = ""
    artifact_ref: Optional[str] = None
    schema_version: str = "1.0"
    lineage: List[str] = field(default_factory=list)

    def is_live(self) -> bool:
        return self.data_mode in LIVE_MODES


@dataclass
class Gap:
    code: str
    detail: str = ""
    addressable: bool = True
    attributes: Dict[str, Any] = field(default_factory=dict)

    def key(self) -> Dict[str, Any]:
        return {"code": self.code, "attributes": self.attributes}


def fingerprint(gaps: List[Gap]) -> str:
    """SHA-256 digest of a canonical serialisation of the unresolved gap set.

    Deterministic and order-independent: the same set of (code, attributes)
    always yields the same digest, so a recurring gap set is detectable.
    """
    items = sorted(
        (g.key() for g in gaps),
        key=lambda d: (d["code"], json.dumps(d["attributes"], sort_keys=True)),
    )
    canon = json.dumps(items, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()
