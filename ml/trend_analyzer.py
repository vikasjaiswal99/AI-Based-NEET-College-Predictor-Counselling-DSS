"""
ml/trend_analyzer.py
====================
Analyze multi-year cutoff trends for colleges.
Detects rising/falling/stable patterns across years.
"""
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger("ml.trend")


@dataclass
class TrendPoint:
    year: int
    closing_rank: int


@dataclass
class CollegeTrend:
    college_name: str
    state: str
    category: str
    quota: str
    data_points: list[TrendPoint]
    direction: str          # "rising", "falling", "stable"
    direction_icon: str     # ↑ ↓ →
    avg_yearly_change: float  # Average rank change per year (negative = harder to get in)
    latest_rank: int
    oldest_rank: int

    def to_dict(self) -> dict:
        return {
            "college_name": self.college_name,
            "state": self.state,
            "category": self.category,
            "quota": self.quota,
            "data_points": [{"year": p.year, "closing_rank": p.closing_rank} for p in self.data_points],
            "direction": self.direction,
            "direction_icon": self.direction_icon,
            "avg_yearly_change": round(self.avg_yearly_change, 1),
            "latest_rank": self.latest_rank,
            "oldest_rank": self.oldest_rank,
        }


class TrendAnalyzer:
    """Analyze cutoff trends from multi-year CSV data."""

    STABLE_THRESHOLD = 0.05  # ±5% change is considered stable

    def __init__(self, data: list[dict]):
        """
        Args:
            data: Raw CSV rows (list of dicts with college_name, category, quota, year, closing_rank).
        """
        self._data = data
        logger.info("TrendAnalyzer initialized with %d rows", len(data))

    def get_trend(
        self,
        college_name: str,
        category: str = "GEN",
        quota: str = "AIQ",
    ) -> Optional[CollegeTrend]:
        """Get cutoff trend for a specific college, category, and quota."""
        rows = [
            r for r in self._data
            if r["college_name"] == college_name
            and r["category"] == category
            and r["quota"] == quota
        ]
        if len(rows) < 2:
            return None

        # Sort by year ascending
        rows.sort(key=lambda r: int(r["year"]))

        points = [TrendPoint(year=int(r["year"]), closing_rank=int(r["closing_rank"])) for r in rows]
        latest = points[-1].closing_rank
        oldest = points[0].closing_rank

        # Calculate average yearly change
        year_span = points[-1].year - points[0].year
        if year_span == 0:
            return None

        total_change = latest - oldest
        avg_change = total_change / year_span
        pct_change = abs(total_change) / max(oldest, 1)

        # Determine direction
        if pct_change < self.STABLE_THRESHOLD:
            direction = "stable"
            icon = "→"
        elif total_change > 0:
            # Closing rank increased = easier to get in = "easing"
            direction = "easing"
            icon = "📉"
        else:
            # Closing rank decreased = harder to get in = "tightening"
            direction = "tightening"
            icon = "📈"

        return CollegeTrend(
            college_name=college_name,
            state=rows[0].get("state", ""),
            category=category,
            quota=quota,
            data_points=points,
            direction=direction,
            direction_icon=icon,
            avg_yearly_change=avg_change,
            latest_rank=latest,
            oldest_rank=oldest,
        )

    def get_all_trends(
        self,
        category: str = "GEN",
        quota: str = "AIQ",
        min_years: int = 2,
    ) -> list[CollegeTrend]:
        """Get trends for all colleges matching the filters."""
        # Group by college
        college_names = set()
        for r in self._data:
            if r["category"] == category and r["quota"] == quota:
                college_names.add(r["college_name"])

        trends = []
        for name in sorted(college_names):
            trend = self.get_trend(name, category, quota)
            if trend and len(trend.data_points) >= min_years:
                trends.append(trend)

        return trends

    def get_tightening_colleges(
        self,
        category: str = "GEN",
        quota: str = "AIQ",
        top_n: int = 10,
    ) -> list[CollegeTrend]:
        """Get colleges where cutoffs are getting tighter (harder to get in)."""
        trends = self.get_all_trends(category, quota)
        tightening = [t for t in trends if t.direction == "tightening"]
        tightening.sort(key=lambda t: t.avg_yearly_change)  # Most negative first
        return tightening[:top_n]

    def get_easing_colleges(
        self,
        category: str = "GEN",
        quota: str = "AIQ",
        top_n: int = 10,
    ) -> list[CollegeTrend]:
        """Get colleges where cutoffs are easing (easier to get in)."""
        trends = self.get_all_trends(category, quota)
        easing = [t for t in trends if t.direction == "easing"]
        easing.sort(key=lambda t: t.avg_yearly_change, reverse=True)  # Most positive first
        return easing[:top_n]
