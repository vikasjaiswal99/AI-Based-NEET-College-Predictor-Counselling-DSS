"""
ml/ml_model.py — NEET College Predictor (CSV-based engine)

This version avoids pandas/numpy so the Django app can run in environments
where building those packages is not possible.
"""
import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger("ml.model")

DEFAULT_CSV_PATH = Path(__file__).resolve().parent / "data" / "neet_cutoffs.csv"
TOP_N_DEFAULT = 10

VALID_CATEGORIES = {"GEN", "OBC", "SC", "ST", "EWS", "GEN-PH", "OBC-PH", "SC-PH", "ST-PH"}
VALID_QUOTAS = {"AIQ", "SQ", "MQ"}

REQUIRED_COLUMNS = {
    "college_name",
    "state",
    "city",
    "college_type",
    "quota",
    "category",
    "opening_rank",
    "closing_rank",
    "annual_fee",
    "year",
    "mbbs_seats",
    "nmc_ranking",
}

# NEET Score → Approximate Rank conversion table
# Based on historical MCC data patterns (2021-2024)
SCORE_TO_RANK_TABLE = [
    (720, 1), (710, 15), (700, 70), (690, 200), (680, 500),
    (670, 1000), (660, 2000), (650, 3500), (640, 6000), (630, 9000),
    (620, 13000), (610, 18000), (600, 25000), (590, 33000), (580, 42000),
    (570, 53000), (560, 65000), (550, 80000), (540, 97000), (530, 115000),
    (520, 135000), (510, 158000), (500, 183000), (490, 210000), (480, 240000),
    (470, 275000), (460, 315000), (450, 360000), (440, 410000), (430, 465000),
    (420, 525000), (410, 590000), (400, 660000), (390, 735000), (380, 815000),
    (370, 900000), (360, 990000), (350, 1085000), (340, 1185000), (330, 1290000),
    (320, 1400000), (310, 1520000), (300, 1645000), (200, 1900000), (100, 2000000),
]


def score_to_rank(score: int) -> int:
    """Convert NEET score (0-720) to approximate All India Rank."""
    if score >= 720:
        return 1
    if score <= 100:
        return 2_000_000
    # Linear interpolation between table entries
    for i in range(len(SCORE_TO_RANK_TABLE) - 1):
        s1, r1 = SCORE_TO_RANK_TABLE[i]
        s2, r2 = SCORE_TO_RANK_TABLE[i + 1]
        if s2 <= score <= s1:
            frac = (s1 - score) / (s1 - s2)
            return int(r1 + frac * (r2 - r1))
    return 2_000_000


@dataclass
class StudentInput:
    rank: int
    category: str
    state: Optional[str] = None
    quota: Optional[str] = None
    college_type: Optional[str] = None
    course: str = 'MBBS'
    top_n: int = TOP_N_DEFAULT

    def __post_init__(self) -> None:
        if not isinstance(self.rank, int) or self.rank < 1:
            raise ValueError(f"rank must be a positive integer, got: {self.rank!r}")
        self.category = self.category.strip().upper()
        if self.category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category '{self.category}'. Choose from: {sorted(VALID_CATEGORIES)}")
        if self.state:
            self.state = self.state.strip().title()
        if self.quota:
            self.quota = self.quota.strip().upper()
            if self.quota not in VALID_QUOTAS:
                raise ValueError(f"Invalid quota '{self.quota}'")
        if self.college_type:
            self.college_type = self.college_type.strip().upper()
        self.course = self.course.strip().upper() if self.course else 'MBBS'
        if self.top_n < 1:
            raise ValueError("top_n must be at least 1.")


@dataclass
class CollegeRecommendation:
    rank_position: int
    college_name: str
    state: str
    city: str
    college_type: str
    quota: str
    category: str
    opening_rank: int
    closing_rank: int
    annual_fee: float
    mbbs_seats: int
    nmc_ranking: Optional[int]
    course_type: str
    bond_years: int
    bond_penalty: float
    year: int
    chance_label: str
    rank_gap: int

    def to_dict(self) -> dict:
        return {
            "rank_position": self.rank_position,
            "college_name": self.college_name,
            "state": self.state,
            "city": self.city,
            "college_type": self.college_type,
            "quota": self.quota,
            "category": self.category,
            "opening_rank": self.opening_rank,
            "closing_rank": self.closing_rank,
            "annual_fee": self.annual_fee,
            "year": self.year,
            "mbbs_seats": self.mbbs_seats,
            "nmc_ranking": self.nmc_ranking,
            "course_type": self.course_type,
            "bond_years": self.bond_years,
            "bond_penalty": self.bond_penalty,
            "chance_label": self.chance_label,
            "rank_gap": self.rank_gap,
        }


class NEETCollegePredictor:
    def __init__(self, csv_path: str | Path = None):
        logger.info("Predictor ready | Using SQLite ORM")
        self._cached_df = None

    @property
    def _df(self):
        """Dynamic backwards compatibility property for views.py and trend_analyzer.py.
        Cached for performance during the lifetime of this Predictor instance.
        """
        if self._cached_df is not None:
            return self._cached_df

        from apps.predictions.models import CollegeCutoff
        qs = CollegeCutoff.objects.all()
        self._cached_df = [
            {
                "college_name": obj.college_name,
                "state": obj.state,
                "city": obj.city,
                "college_type": obj.college_type,
                "quota": obj.quota,
                "category": obj.category,
                "opening_rank": obj.opening_rank,
                "closing_rank": obj.closing_rank,
                "annual_fee": obj.annual_fee,
                "year": obj.year,
                "mbbs_seats": obj.mbbs_seats,
                "nmc_ranking": obj.nmc_ranking,
                "course_type": obj.course_type,
                "bond_years": obj.bond_years,
                "bond_penalty": obj.bond_penalty,
            } for obj in qs
        ]
        return self._cached_df

    def predict(
        self,
        rank: int,
        category: str,
        state: Optional[str] = None,
        quota: Optional[str] = None,
        college_type: Optional[str] = None,
        course: str = 'MBBS',
        top_n: int = TOP_N_DEFAULT,
        **kwargs
    ) -> list[CollegeRecommendation]:
        student = StudentInput(
            rank=rank, category=category, state=state, quota=quota, 
            college_type=college_type, course=course, top_n=top_n
        )

        filtered = self._apply_filters(student)
        if not filtered:
            return []

        filtered = sorted(filtered, key=lambda r: r["closing_rank"], reverse=False)
        head = filtered[: student.top_n]

        return [
            self._build_recommendation(idx + 1, row, student.rank)
            for idx, row in enumerate(head)
        ]

    def predict_as_dicts(self, **kwargs) -> list[dict]:
        return [r.to_dict() for r in self.predict(**kwargs)]

    def _apply_filters(self, student: StudentInput) -> list[dict[str, Any]]:
        from apps.predictions.models import CollegeCutoff
        from django.db.models import Q
        
        rank = student.rank
        
        # Base filters
        qs = CollegeCutoff.objects.filter(
            category=student.category, 
            closing_rank__gte=rank,
            course_type__iexact=student.course
        )
        
        if student.quota:
            qs = qs.filter(quota=student.quota)
        if student.college_type:
            qs = qs.filter(college_type=student.college_type)
        if student.state:
            # state match OR AIQ seats
            qs = qs.filter(Q(state__iexact=student.state) | Q(quota='AIQ'))
            
        results = []
        for obj in qs:
            row = {
                "college_name": obj.college_name,
                "state": obj.state,
                "city": obj.city,
                "college_type": obj.college_type,
                "quota": obj.quota,
                "category": obj.category,
                "opening_rank": obj.opening_rank,
                "closing_rank": obj.closing_rank,
                "annual_fee": obj.annual_fee,
                "year": obj.year,
                "mbbs_seats": obj.mbbs_seats,
                "nmc_ranking": obj.nmc_ranking,
                "course_type": obj.course_type,
                "bond_years": obj.bond_years,
                "bond_penalty": obj.bond_penalty,
            }
            results.append(row)

        return results

    @staticmethod
    def _chance_label(closing_rank: int, student_rank: int) -> str:
        gap = closing_rank - student_rank
        if gap >= 5000:
            return "SAFE"
        if gap >= 1000:
            return "MODERATE"
        return "AMBITIOUS"

    @staticmethod
    def _build_recommendation(
        position: int,
        row: dict[str, Any],
        student_rank: int,
    ) -> CollegeRecommendation:
        cr = int(row["closing_rank"])
        return CollegeRecommendation(
            rank_position=position,
            college_name=row["college_name"],
            state=row["state"],
            city=row.get("city", ""),
            college_type=row["college_type"],
            quota=row["quota"],
            category=row["category"],
            opening_rank=int(row["opening_rank"]),
            closing_rank=cr,
            annual_fee=float(row["annual_fee"]),
            year=int(row["year"]),
            mbbs_seats=int(row.get("mbbs_seats", 0)),
            nmc_ranking=int(row.get("nmc_ranking") or 0) if row.get("nmc_ranking") is not None else None,
            course_type=row.get("course_type", "MBBS"),
            bond_years=int(row.get("bond_years") or 0),
            bond_penalty=float(row.get("bond_penalty") or 0),
            chance_label=NEETCollegePredictor._chance_label(cr, student_rank),
            rank_gap=cr - student_rank,
        )
