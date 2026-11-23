"""Three-valued release policy and its mandatory checks.

The policy is deterministic and takes no language-model output as an input to the
verdict derivation. Each mandatory check yields PASS / BLOCK / NOT_EVALUABLE, and
the overall verdict is:

    BLOCK          if any check is BLOCK
    NOT_EVALUABLE  else if any check is NOT_EVALUABLE
    PASS           else (every mandatory check is PASS)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

from .model import CheckOutcome, EvidenceRecord, Verdict
from .validator import ValidationResult


@dataclass
class WarningFeed:
    """An official warning feed. `connected=False` means the input is unavailable."""
    connected: bool = False
    active_warning: bool = False
    source: str = "reference_warning_feed"


@dataclass
class ProtectedArea:
    name: str
    center_lat: float
    center_lon: float
    radius_km: float


@dataclass
class VesselThresholds:
    """Expert-reviewed per-vessel limits. `approved=False` means not yet reviewed."""
    max_wave_height_m: float
    max_wind_speed_kmh: float
    approved: bool = False
    vessel: str = "motorized_craft"


@dataclass
class ReleaseContext:
    target: Tuple[float, float]
    records: List[EvidenceRecord]
    warning_feed: Optional[WarningFeed] = None          # None => input unavailable
    protected_areas: Optional[List[ProtectedArea]] = None  # None => geometry unavailable
    vessel_thresholds: Optional[VesselThresholds] = None   # None => thresholds unavailable


@dataclass
class PolicyResult:
    verdict: Verdict
    checks: List[Tuple[str, CheckOutcome, str]] = field(default_factory=list)

    def can_release(self) -> bool:
        return self.verdict == CheckOutcome.PASS


def _haversine_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    from math import radians, sin, cos, asin, sqrt
    lat1, lon1, lat2, lon2 = map(radians, (a[0], a[1], b[0], b[1]))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371.0 * asin(sqrt(h))


class ReleasePolicy:
    """Evaluates mandatory release checks and derives the overall verdict."""

    def evaluate(self, ctx: ReleaseContext, validation: ValidationResult) -> PolicyResult:
        checks: List[Tuple[str, CheckOutcome, str]] = []
        checks.append(self._official_warning(ctx))
        checks.append(self._protected_area(ctx))
        checks.append(self._vessel_limits(ctx, validation))
        checks.append(self._evidence_adequacy(validation))
        verdict = self._derive(checks)
        return PolicyResult(verdict=verdict, checks=checks)

    # --- individual mandatory checks -------------------------------------
    def _official_warning(self, ctx: ReleaseContext):
        feed = ctx.warning_feed
        if feed is None or not feed.connected:
            return ("official_warning_absent", CheckOutcome.NOT_EVALUABLE,
                    "no authoritative warning feed connected")
        if feed.active_warning:
            return ("official_warning_absent", CheckOutcome.BLOCK, "active official warning in force")
        return ("official_warning_absent", CheckOutcome.PASS, "no active warning")

    def _protected_area(self, ctx: ReleaseContext):
        areas = ctx.protected_areas
        if areas is None:
            return ("protected_area_clearance", CheckOutcome.NOT_EVALUABLE,
                    "no protected-area geometry integrated")
        for a in areas:
            if _haversine_km(ctx.target, (a.center_lat, a.center_lon)) <= a.radius_km:
                return ("protected_area_clearance", CheckOutcome.BLOCK, f"inside {a.name}")
        return ("protected_area_clearance", CheckOutcome.PASS, "clear of protected areas")

    def _vessel_limits(self, ctx: ReleaseContext, validation: ValidationResult):
        th = ctx.vessel_thresholds
        if th is None or not th.approved:
            return ("vessel_limits", CheckOutcome.NOT_EVALUABLE,
                    "no expert-reviewed vessel thresholds")
        if not validation.core_evidence_ok():
            return ("vessel_limits", CheckOutcome.NOT_EVALUABLE,
                    "core evidence missing; cannot compare to limits")
        wave = next((r.value for r in ctx.records
                     if r.parameter == "wave_height_m" and r.value is not None and r.is_live()), None)
        wind = next((r.value for r in ctx.records
                     if r.parameter == "wind_speed_kmh" and r.value is not None and r.is_live()), None)
        if wave is not None and wave > th.max_wave_height_m:
            return ("vessel_limits", CheckOutcome.BLOCK,
                    f"wave {wave}m > limit {th.max_wave_height_m}m")
        if wind is not None and wind > th.max_wind_speed_kmh:
            return ("vessel_limits", CheckOutcome.BLOCK,
                    f"wind {wind}km/h > limit {th.max_wind_speed_kmh}km/h")
        return ("vessel_limits", CheckOutcome.PASS, "within vessel limits")

    def _evidence_adequacy(self, validation: ValidationResult):
        if validation.has_blocking_defect():
            return ("evidence_adequacy", CheckOutcome.BLOCK, "evidence has a non-recoverable defect")
        if not validation.core_evidence_ok() or validation.has_addressable_gap():
            return ("evidence_adequacy", CheckOutcome.NOT_EVALUABLE, "evidence gap present")
        return ("evidence_adequacy", CheckOutcome.PASS, "evidence adequate")

    # --- deterministic derivation ----------------------------------------
    @staticmethod
    def _derive(checks) -> Verdict:
        outcomes = [o for _, o, _ in checks]
        if any(o == CheckOutcome.BLOCK for o in outcomes):
            return CheckOutcome.BLOCK
        if any(o == CheckOutcome.NOT_EVALUABLE for o in outcomes):
            return CheckOutcome.NOT_EVALUABLE
        return CheckOutcome.PASS
