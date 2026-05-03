"""
ml/college_scorer.py — 100-Point College Fitness Scoring System

Formula (total = 100):
  A. Rank Proximity  : max 60 pts
  B. State Match     : max 25 pts
  C. Category Bonus  : max 15 pts
"""
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .ml_model import DEFAULT_CSV_PATH
from .counselling_strategy import CounsellingStrategyEngine, StrategyEntry, Tier, CounsellingStrategy

logger = logging.getLogger('ml.scorer')

WEIGHT_RANK  : int   = 60
WEIGHT_STATE : int   = 25
WEIGHT_CAT   : int   = 15
PROXIMITY_CAP: float = 3.0
RESERVED_CATEGORIES = {'OBC', 'SC', 'ST', 'EWS', 'OBC-PH', 'SC-PH', 'ST-PH'}


@dataclass
class ScoreBreakdown:
    rank_proximity_score  : float
    state_match_score     : float
    category_bonus_score  : float
    total_score           : float
    score_label           : str
    rank_proximity_reason : str
    state_match_reason    : str
    category_bonus_reason : str

    @property
    def formatted(self) -> str:
        return f'Score: {self.total_score:.1f}%'

    def to_dict(self) -> dict:
        return {
            'total_score' : round(self.total_score, 1),
            'formatted'   : self.formatted,
            'score_label' : self.score_label,
            'breakdown'   : {
                'rank_proximity': {'score': round(self.rank_proximity_score, 1), 'max': WEIGHT_RANK,  'reason': self.rank_proximity_reason},
                'state_match'   : {'score': round(self.state_match_score, 1),   'max': WEIGHT_STATE, 'reason': self.state_match_reason},
                'category_bonus': {'score': round(self.category_bonus_score, 1),'max': WEIGHT_CAT,   'reason': self.category_bonus_reason},
            },
        }


@dataclass
class ScoredCollege:
    college               : str
    state                 : str
    city                  : str
    college_type          : str
    quota                 : str
    category              : str
    closing_rank          : int
    annual_fee            : float
    mbbs_seats            : int
    nmc_ranking           : Optional[int]
    course_type           : str
    bond_years            : int
    bond_penalty          : float
    tier                  : Tier
    rank_gap              : int
    admission_probability : float
    advice                : str
    score                 : ScoreBreakdown

    @property
    def display_line(self) -> str:
        return f'{self.college} | {self.score.formatted}'

    def to_dict(self) -> dict:
        return {
            'college'               : self.college,
            'state'                 : self.state,
            'city'                  : self.city,
            'college_type'          : self.college_type,
            'quota'                 : self.quota,
            'category'              : self.category,
            'closing_rank'          : self.closing_rank,
            'annual_fee'            : self.annual_fee,
            'mbbs_seats'            : self.mbbs_seats,
            'nmc_ranking'           : self.nmc_ranking,
            'tier'                  : self.tier.value if isinstance(self.tier, Tier) else self.tier,
            'rank_gap'              : self.rank_gap,
            'admission_probability' : round(self.admission_probability, 3),
            'advice'                : self.advice,
            'score'                 : self.score.to_dict(),
        }


class CollegeScorer:
    def score(self, entry: StrategyEntry, student_rank: int,
              student_state: Optional[str], student_category: str) -> ScoredCollege:
        comp_a, reason_a = self._rank_proximity(entry.closing_rank, student_rank)
        comp_b, reason_b = self._state_match(entry.state, entry.quota, student_state or '')
        comp_c, reason_c = self._category_bonus(student_category.upper(), entry.college_type)
        total = round(min(comp_a + comp_b + comp_c, 100.0), 1)
        breakdown = ScoreBreakdown(
            rank_proximity_score=round(comp_a, 1), state_match_score=round(comp_b, 1),
            category_bonus_score=round(comp_c, 1), total_score=total,
            score_label=self._label(total),
            rank_proximity_reason=reason_a, state_match_reason=reason_b, category_bonus_reason=reason_c,
        )
        return ScoredCollege(
            college=entry.college, state=entry.state, city=entry.city,
            college_type=entry.college_type,
            quota=entry.quota, category=entry.category, closing_rank=entry.closing_rank,
            annual_fee=entry.annual_fee, mbbs_seats=entry.mbbs_seats,
            nmc_ranking=entry.nmc_ranking, course_type=entry.course_type,
            bond_years=entry.bond_years, bond_penalty=entry.bond_penalty,
            tier=entry.tier, rank_gap=entry.rank_gap,
            admission_probability=entry.admission_probability, advice=entry.advice, score=breakdown,
        )

    def score_all(self, entries: list[StrategyEntry], student_rank: int,
                  student_state: Optional[str], student_category: str) -> list[ScoredCollege]:
        return sorted(
            [self.score(e, student_rank, student_state, student_category) for e in entries],
            key=lambda x: -x.score.total_score,
        )

    @staticmethod
    def _rank_proximity(closing_rank: int, student_rank: int) -> tuple[float, str]:
        if student_rank <= 0: return 0.0, 'Invalid rank.'
        if closing_rank >= student_rank:
            ratio  = closing_rank / student_rank
            capped = min(ratio, PROXIMITY_CAP)
            score  = (capped / PROXIMITY_CAP) * WEIGHT_RANK
            pct    = ((closing_rank - student_rank) / student_rank) * 100
            reason = (f'Cutoff ({closing_rank:,}) is {pct:.1f}% above your rank ({student_rank:,}). '
                      f'Ratio {ratio:.2f}× → {score:.1f}/{WEIGHT_RANK} pts.')
        else:
            gap_frac = (student_rank - closing_rank) / student_rank
            score    = max(0.0, (1.0 - gap_frac) * (WEIGHT_RANK / 2))
            reason   = (f'Your rank ({student_rank:,}) exceeds cutoff ({closing_rank:,}) '
                        f'by {gap_frac*100:.1f}% — Dream. Partial credit: {score:.1f}/{WEIGHT_RANK} pts.')
        return score, reason

    @staticmethod
    def _state_match(college_state: str, quota: str, student_state: str) -> tuple[float, str]:
        same  = college_state.strip().lower() == student_state.strip().lower() if student_state else False
        is_sq = quota.upper() == 'SQ'
        if same and is_sq:
            return WEIGHT_STATE, f'Home state ({college_state}) + SQ — maximum advantage. 25/{WEIGHT_STATE} pts.'
        if same:
            s = WEIGHT_STATE * 0.60
            return s, f'Home state ({college_state}) + AIQ — partial advantage. {s:.1f}/{WEIGHT_STATE} pts.'
        if not is_sq:
            s = WEIGHT_STATE * 0.40
            return s, f'Out-of-state + AIQ — neutral pan-India. {s:.1f}/{WEIGHT_STATE} pts.'
        return 0.0, f'Out-of-state + SQ — SQ unavailable for non-domicile. 0/{WEIGHT_STATE} pts.'

    @staticmethod
    def _category_bonus(category: str, college_type: str) -> tuple[float, str]:
        base, bonus = 10.0, 0.0
        reasons = [f'Category match ({category}): {base:.0f} pts base.']
        if category in RESERVED_CATEGORIES and college_type.upper() == 'GOVT':
            bonus = 5.0
            reasons.append(f'Reserved + GOVT → +{bonus:.0f} pts (mandated seats).')
        elif category not in RESERVED_CATEGORIES and college_type.upper() in {'PRIVATE', 'DEEMED'}:
            bonus = 3.0
            reasons.append(f'GEN + {college_type} → +{bonus:.0f} pts (less reservation competition).')
        else:
            reasons.append('No additional structural advantage.')
        return min(base + bonus, WEIGHT_CAT), ' '.join(reasons)

    @staticmethod
    def _label(score: float) -> str:
        if score >= 80: return 'Excellent'
        if score >= 60: return 'Good'
        if score >= 40: return 'Fair'
        return 'Low'


class ScoredPredictionPipeline:
    """
    End-to-end pipeline: CSV → filter → tier classify → score → sorted output.
    Instantiate once (module-level singleton in views.py) for performance.
    """
    def __init__(self, csv_path: str | Path = DEFAULT_CSV_PATH):
        self._engine = CounsellingStrategyEngine(csv_path)
        self._scorer = CollegeScorer()
        logger.info('ScoredPredictionPipeline ready.')

    def run(self, rank: int, category: str, state: Optional[str] = None,
            quota: Optional[str] = None, sort_by: str = 'score',
            college_type: Optional[str] = None, course: str = 'MBBS') -> list[ScoredCollege]:
        strategy = self._engine.build_strategy(rank=rank, category=category, state=state,
                                                quota=quota, college_type=college_type, course=course)
        if not strategy.all_colleges:
            return []
        scored = self._scorer.score_all(strategy.all_colleges, rank, state, category)
        return self._sort(scored, sort_by)

    def run_as_dicts(self, **kwargs) -> list[dict]:
        return [c.to_dict() for c in self.run(**kwargs)]

    @staticmethod
    def _sort(colleges: list[ScoredCollege], sort_by: str) -> list[ScoredCollege]:
        if sort_by == 'tier':
            order = {Tier.SAFE: 0, Tier.TARGET: 1, Tier.DREAM: 2}
            return sorted(colleges, key=lambda c: (order.get(c.tier, 3), -c.score.total_score))
        if sort_by == 'closing_rank':
            return sorted(colleges, key=lambda c: c.closing_rank)
        return sorted(colleges, key=lambda c: -c.score.total_score)
