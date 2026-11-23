"""Evidence validator: applies rule checks to evidence records and emits gaps."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from .model import CheckOutcome, EvidenceRecord, Gap

CORE_PARAMS = ("wave_height_m", "wind_speed_kmh")

PHYSICAL_RANGES = {
    "wave_height_m": (0.0, 30.0),
    "wind_speed_kmh": (0.0, 400.0),
    "current_speed_ms": (0.0, 10.0),
}
EXPECTED_UNITS = {
    "wave_height_m": "m",
    "wind_speed_kmh": "km/h",
    "current_speed_ms": "m/s",
}


class ValidationResult:
    def __init__(self) -> None:
        self.checks: List[Tuple[str, CheckOutcome, str]] = []
        self.gaps: List[Gap] = []

    def record(self, name: str, outcome: CheckOutcome, detail: str = "") -> None:
        self.checks.append((name, outcome, detail))

    def add_gap(self, gap: Gap) -> None:
        self.gaps.append(gap)

    @property
    def gap_codes(self) -> List[str]:
        return sorted(g.code for g in self.gaps)

    def has_addressable_gap(self) -> bool:
        return any(g.addressable for g in self.gaps)

    def core_evidence_ok(self) -> bool:
        return not any(g.code == "MISSING_CORE_EVIDENCE" for g in self.gaps)

    def has_blocking_defect(self) -> bool:
        return any(not g.addressable for g in self.gaps)


class EvidenceValidator:
    def __init__(
        self,
        freshness_max_age_s: int = 6 * 3600,
        target: Optional[Tuple[float, float]] = None,
        coverage_radius_km: float = 50.0,
        now: Optional[datetime] = None,
    ) -> None:
        self.freshness_max_age_s = freshness_max_age_s
        self.target = target
        self.coverage_radius_km = coverage_radius_km
        self._now = now

    def _now_utc(self) -> datetime:
        return self._now or datetime.now(timezone.utc)

    @staticmethod
    def _parse(t: Optional[str]) -> Optional[datetime]:
        if not t:
            return None
        try:
            return datetime.fromisoformat(t.replace("Z", "+00:00"))
        except Exception:
            return None

    @staticmethod
    def _haversine_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
        from math import radians, sin, cos, asin, sqrt
        lat1, lon1, lat2, lon2 = map(radians, (a[0], a[1], b[0], b[1]))
        dlat, dlon = lat2 - lat1, lon2 - lon1
        h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        return 2 * 6371.0 * asin(sqrt(h))

    def validate(self, records: List[EvidenceRecord]) -> ValidationResult:
        r = ValidationResult()
        by_param = {}
        for rec in records:
            by_param.setdefault(rec.parameter, []).append(rec)

        # structure
        structural_ok = all(isinstance(x, EvidenceRecord) and x.parameter for x in records)
        r.record("structure", CheckOutcome.PASS if structural_ok else CheckOutcome.BLOCK)
        if not structural_ok:
            r.add_gap(Gap("MALFORMED_RECORD", "record missing parameter", addressable=False))

        # evidence presence
        if not records:
            r.record("evidence_presence", CheckOutcome.NOT_EVALUABLE, "no records")
            r.add_gap(Gap("NO_EVIDENCE", "no evidence records", addressable=True))
        else:
            r.record("evidence_presence", CheckOutcome.PASS)

        # core-evidence presence (live value required)
        missing_core = []
        for p in CORE_PARAMS:
            recs = by_param.get(p, [])
            if not recs or all((x.value is None or not x.is_live()) for x in recs):
                missing_core.append(p)
        if missing_core:
            r.record("core_evidence_presence", CheckOutcome.NOT_EVALUABLE, f"missing live core: {missing_core}")
            for p in missing_core:
                r.add_gap(Gap("MISSING_CORE_EVIDENCE", f"missing live {p}",
                              addressable=True, attributes={"parameter": p}))
        else:
            r.record("core_evidence_presence", CheckOutcome.PASS)

        # units
        unit_bad = sorted({x.parameter for x in records
                           if x.parameter in EXPECTED_UNITS and x.unit != EXPECTED_UNITS[x.parameter]})
        if unit_bad:
            r.record("units", CheckOutcome.BLOCK, f"unit mismatch: {unit_bad}")
            r.add_gap(Gap("UNIT_MISMATCH", str(unit_bad), addressable=False, attributes={"parameters": unit_bad}))
        else:
            r.record("units", CheckOutcome.PASS)

        # physical range
        oor = sorted({x.parameter for x in records
                      if x.value is not None and x.parameter in PHYSICAL_RANGES
                      and not (PHYSICAL_RANGES[x.parameter][0] <= x.value <= PHYSICAL_RANGES[x.parameter][1])})
        if oor:
            r.record("physical_range", CheckOutcome.BLOCK, f"out of range: {oor}")
            r.add_gap(Gap("OUT_OF_RANGE", str(oor), addressable=False, attributes={"parameters": oor}))
        else:
            r.record("physical_range", CheckOutcome.PASS)

        # freshness
        now = self._now_utc()
        stale = []
        for x in records:
            if x.value is None:
                continue
            t = self._parse(x.valid_time or x.obs_time or x.retrieval_time)
            if t is None:
                continue
            if (now - t).total_seconds() > self.freshness_max_age_s:
                stale.append(x.parameter)
        stale = sorted(set(stale))
        if stale:
            r.record("freshness", CheckOutcome.NOT_EVALUABLE, f"stale: {stale}")
            for p in stale:
                r.add_gap(Gap("STALE_EVIDENCE", f"stale {p}", addressable=True, attributes={"parameter": p}))
        else:
            r.record("freshness", CheckOutcome.PASS)

        # spatial coverage
        if self.target is not None:
            far = sorted({x.parameter for x in records
                          if x.value is not None
                          and self._haversine_km(self.target, (x.lat, x.lon)) > self.coverage_radius_km})
            if far:
                r.record("spatial_coverage", CheckOutcome.NOT_EVALUABLE, f"outside coverage: {far}")
                for p in far:
                    r.add_gap(Gap("SPATIAL_MISMATCH", f"{p} outside {self.coverage_radius_km} km",
                                  addressable=True, attributes={"parameter": p}))
            else:
                r.record("spatial_coverage", CheckOutcome.PASS)
        else:
            r.record("spatial_coverage", CheckOutcome.NOT_EVALUABLE, "no target")

        # value consistency (same parameter, diverging live values)
        inconsistent = []
        for p, recs in by_param.items():
            vals = [x.value for x in recs if x.value is not None]
            if len(vals) >= 2 and (max(vals) - min(vals)) > 0.5 * (abs(sum(vals) / len(vals)) + 1e-9):
                inconsistent.append(p)
        inconsistent = sorted(set(inconsistent))
        if inconsistent:
            r.record("value_consistency", CheckOutcome.BLOCK, f"inconsistent: {inconsistent}")
            r.add_gap(Gap("VALUE_MISMATCH", str(inconsistent), addressable=False,
                          attributes={"parameters": inconsistent}))
        else:
            r.record("value_consistency", CheckOutcome.PASS)

        # attribution + artefact existence (PASS when present)
        unattributed = [x.parameter for x in records if not x.attribution]
        r.record("attribution", CheckOutcome.PASS if not unattributed else CheckOutcome.NOT_EVALUABLE,
                 "" if not unattributed else f"missing attribution: {sorted(set(unattributed))}")

        # shared-lineage (further embodiment): corroborating records sharing a parent
        # are flagged as not-independent (informational; does not itself block).
        for p, recs in by_param.items():
            parents = [tuple(sorted(x.lineage)) for x in recs if x.lineage]
            if len(parents) >= 2 and len(set(parents)) == 1:
                r.record("shared_lineage", CheckOutcome.PASS, f"{p}: corroboration not independent (shared lineage)")
                break
        else:
            r.record("shared_lineage", CheckOutcome.PASS)

        return r
