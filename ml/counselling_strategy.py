"""
ml/counselling_strategy.py — Dream / Target / Safe Classification Engine

Refactored to remove the pandas dependency so the Django app can start in
environments where pandas can't be built/installed.
"""
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Any

from .ml_model import NEETCollegePredictor, StudentInput, DEFAULT_CSV_PATH

logger = logging.getLogger("ml.strategy")

SAFE_MULTIPLIER: float = 1.5
TIER_LIMITS = {"Dream": 10, "Target": 20, "Safe": 20}


class Tier(str, Enum):
    DREAM = "Dream"
    TARGET = "Target"
    SAFE = "Safe"


@dataclass
class StrategyEntry:
    college: str
    state: str
    city: str
    college_type: str
    quota: str
    category: str
    closing_rank: int
    annual_fee: float
    mbbs_seats: int
    nmc_ranking: Optional[int]
    course_type: str
    bond_years: int
    bond_penalty: float
    tier: Tier
    rank_gap: int
    admission_probability: float
    advice: str

    def to_dict(self) -> dict:
        return {
            "college": self.college,
            "state": self.state,
            "city": self.city,
            "college_type": self.college_type,
            "quota": self.quota,
            "category": self.category,
            "closing_rank": self.closing_rank,
            "annual_fee": self.annual_fee,
            "mbbs_seats": self.mbbs_seats,
            "nmc_ranking": self.nmc_ranking,
            "tier": self.tier.value,
            "rank_gap": self.rank_gap,
            "admission_probability": round(self.admission_probability, 3),
            "advice": self.advice,
        }


@dataclass
class CounsellingStrategy:
    student_rank: int
    student_category: str
    student_state: Optional[str]
    quota: Optional[str]
    dream_colleges: list[StrategyEntry] = field(default_factory=list)
    target_colleges: list[StrategyEntry] = field(default_factory=list)
    safe_colleges: list[StrategyEntry] = field(default_factory=list)

    @property
    def all_colleges(self) -> list[StrategyEntry]:
        return self.dream_colleges + self.target_colleges + self.safe_colleges

    def to_flat_list(self) -> list[dict]:
        return [{"college": e.college if hasattr(e, "college") else e.college, "category": e.tier.value} for e in self.all_colleges]

    def to_dict(self) -> dict:
        return {
            "summary": {
                "student_rank": self.student_rank,
                "total": len(self.all_colleges),
                "dream": len(self.dream_colleges),
                "target": len(self.target_colleges),
                "safe": len(self.safe_colleges),
            },
            "dream_colleges": [e.to_dict() for e in self.dream_colleges],
            "target_colleges": [e.to_dict() for e in self.target_colleges],
            "safe_colleges": [e.to_dict() for e in self.safe_colleges],
        }


class CounsellingStrategyEngine:
    def __init__(self, csv_path: str | Path = DEFAULT_CSV_PATH):
        self._predictor = NEETCollegePredictor(csv_path)
        # NEETCollegePredictor._df is a list[dict] (pure python).
        self._df: list[dict[str, Any]] = self._predictor._df
        logger.info("CounsellingStrategyEngine ready.")

    def build_strategy(
        self,
        rank: int,
        category: str,
        state: Optional[str] = None,
        quota: Optional[str] = None,
        course: str = 'MBBS',
        **kwargs,
    ) -> CounsellingStrategy:
        student = StudentInput(rank=rank, category=category, state=state, quota=quota,
                               college_type=kwargs.get('college_type'), course=course, top_n=999)
        candidates = self._get_candidates(student)
        if not candidates:
            return CounsellingStrategy(rank, category, state, quota)

        candidates_with_tiers = self._assign_tiers(candidates, student.rank)

        def tier_list(tier_value: str) -> list[dict[str, Any]]:
            return [r for r in candidates_with_tiers if r["tier"] == tier_value]

        dream_rows = tier_list(Tier.DREAM.value)
        target_rows = tier_list(Tier.TARGET.value)
        safe_rows = tier_list(Tier.SAFE.value)

        # Match original ordering:
        # - Dream/Target: closing_rank descending
        # - Safe: closing_rank ascending
        dream_rows = sorted(dream_rows, key=lambda r: r["closing_rank"], reverse=True)[: TIER_LIMITS["Dream"]]
        target_rows = sorted(target_rows, key=lambda r: r["closing_rank"], reverse=True)[: TIER_LIMITS["Target"]]
        safe_rows = sorted(safe_rows, key=lambda r: r["closing_rank"], reverse=False)[: TIER_LIMITS["Safe"]]

        return CounsellingStrategy(
            student_rank=rank,
            student_category=category,
            student_state=state,
            quota=quota,
            dream_colleges=self._build_entries(dream_rows, rank, Tier.DREAM),
            target_colleges=self._build_entries(target_rows, rank, Tier.TARGET),
            safe_colleges=self._build_entries(safe_rows, rank, Tier.SAFE),
        )

    def _get_candidates(self, student: StudentInput) -> list[dict[str, Any]]:
        # Filter to category and course
        rows = [r for r in self._df if r["category"] == student.category and str(r["course_type"]).upper() == student.course.upper()]

        # Filter by quota (only if explicitly provided)
        if student.quota:
            rows = [r for r in rows if r["quota"] == student.quota]

        # Filter by college type (GOVT/PRIVATE/DEEMED/CENTRAL)
        if student.college_type:
            rows = [r for r in rows if r["college_type"] == student.college_type]

        # Filter by domicile state (or AIQ seats)
        if student.state:
            state_lower = student.state.lower()
            rows = [
                r
                for r in rows
                if (str(r["state"]).lower() == state_lower) or str(r["quota"]).upper() == "AIQ"
            ]

        # Sort by year desc, drop duplicates subset ['college_name','quota','category']
        rows_sorted = sorted(rows, key=lambda r: r["year"], reverse=True)

        seen: set[tuple[str, str, str]] = set()
        deduped: list[dict[str, Any]] = []
        for r in rows_sorted:
            key = (str(r["college_name"]), str(r["quota"]), str(r["category"]))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(r)

        return deduped

    @staticmethod
    def _assign_tiers(df: list[dict[str, Any]], student_rank: int) -> list[dict[str, Any]]:
        dream_ceiling = student_rank / SAFE_MULTIPLIER

        def classify(cr: float) -> str:
            if cr >= student_rank:
                return Tier.SAFE.value
            if cr >= dream_ceiling:
                return Tier.TARGET.value
            return Tier.DREAM.value

        out: list[dict[str, Any]] = []
        for r in df:
            rr = dict(r)
            rr["tier"] = classify(rr["closing_rank"])
            out.append(rr)
        return out

    @staticmethod
    def _admission_probability(closing_rank: int, student_rank: int) -> float:
        if student_rank == 0:
            return 0.0
        return round(min(closing_rank / student_rank, 1.0) * 0.92, 3)

    @staticmethod
    def _generate_advice(tier: Tier, rank_gap: int, college_type: str, annual_fee: float) -> str:
        financial_note = f" Annual fee is ₹{annual_fee:,.0f}." if annual_fee > 0 else ""
        if tier == Tier.SAFE:
            return (
                f"Safe Option. Your rank is well within the historical closing range (Margin: +{rank_gap:,}).{financial_note}"
                if rank_gap > 5000
                else f"Safe Option. Your rank is within historical closing parameters.{financial_note}"
            )
        if tier == Tier.TARGET:
            return (
                f"Target Option. Your rank is marginally below historical cutoffs (Gap: {abs(rank_gap):,}). "
                f"Admission is achievable within standard statistical variance.{financial_note}"
            )
        return (
            f"Ambitious Option. Statistical probability is low based on historical trends (Gap: {abs(rank_gap):,}). "
            f"Include as an aspirational choice.{financial_note}"
        )

    def _build_entries(self, rows: list[dict[str, Any]], rank: int, tier: Tier) -> list[StrategyEntry]:
        entries: list[StrategyEntry] = []
        for row in rows:
            cr = int(row["closing_rank"])
            rank_gap = cr - rank
            entries.append(
                StrategyEntry(
                    college=row["college_name"],
                    state=row["state"],
                    city=row.get("city", ""),
                    college_type=row["college_type"],
                    quota=row["quota"],
                    category=row["category"],
                    closing_rank=cr,
                    annual_fee=float(row["annual_fee"]),
                    mbbs_seats=int(row.get("mbbs_seats", 0)),
                    nmc_ranking=int(row.get("nmc_ranking") or 0) if row.get("nmc_ranking") is not None else None,
                    course_type=row.get("course_type", "MBBS"),
                    bond_years=int(row.get("bond_years") or 0),
                    bond_penalty=float(row.get("bond_penalty") or 0),
                    tier=tier,
                    rank_gap=rank_gap,
                    admission_probability=self._admission_probability(cr, rank),
                    advice=self._generate_advice(tier, rank_gap, row["college_type"], float(row["annual_fee"])),
                )
            )
        return entries
