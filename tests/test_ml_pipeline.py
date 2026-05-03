"""
tests/test_ml_pipeline.py
Unit tests for the ML prediction pipeline.
Run with: pytest tests/test_ml_pipeline.py -v
"""
import sys
from pathlib import Path
import pytest

# Make ml package importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.ml_model import NEETCollegePredictor, StudentInput, score_to_rank
from ml.counselling_strategy import CounsellingStrategyEngine, Tier
from ml.college_scorer import CollegeScorer, ScoredPredictionPipeline

CSV = Path(__file__).resolve().parent.parent / 'ml' / 'data' / 'neet_cutoffs.csv'


# ── StudentInput validation ────────────────────────────────────────────────

class TestStudentInput:
    def test_valid_input(self):
        s = StudentInput(rank=50000, category='OBC')
        assert s.rank == 50000
        assert s.category == 'OBC'

    def test_category_uppercased(self):
        s = StudentInput(rank=1000, category='obc')
        assert s.category == 'OBC'

    def test_state_title_cased(self):
        s = StudentInput(rank=1000, category='GEN', state='maharashtra')
        assert s.state == 'Maharashtra'

    def test_invalid_rank(self):
        with pytest.raises(ValueError, match='rank'):
            StudentInput(rank=-1, category='GEN')

    def test_invalid_category(self):
        with pytest.raises(ValueError, match='category'):
            StudentInput(rank=1000, category='INVALID')

    def test_invalid_quota(self):
        with pytest.raises(ValueError, match='quota'):
            StudentInput(rank=1000, category='GEN', quota='XYZ')

    def test_college_type_uppercased(self):
        s = StudentInput(rank=1000, category='GEN', college_type='govt')
        assert s.college_type == 'GOVT'

    def test_college_type_none_ok(self):
        s = StudentInput(rank=1000, category='GEN', college_type=None)
        assert s.college_type is None


# ── Score to Rank Conversion ──────────────────────────────────────────────

class TestScoreToRank:
    def test_max_score(self):
        assert score_to_rank(720) == 1

    def test_min_score(self):
        assert score_to_rank(100) == 2_000_000

    def test_mid_range_score(self):
        rank = score_to_rank(550)
        assert 50000 < rank < 120000  # Approximately 80000 range

    def test_high_score(self):
        rank = score_to_rank(700)
        assert rank < 200  # Top ranks

    def test_monotonic_decreasing(self):
        """Higher scores should give lower (better) ranks."""
        ranks = [score_to_rank(s) for s in range(300, 720, 10)]
        for i in range(len(ranks) - 1):
            assert ranks[i] >= ranks[i + 1], \
                f'score_to_rank not monotonic at scores {300 + (i+1)*10} and {300 + i*10}'


# ── Predictor ─────────────────────────────────────────────────────────────────

@pytest.mark.skipif(not CSV.exists(), reason='CSV dataset not found')
class TestNEETCollegePredictor:
    @pytest.fixture(scope='class')
    def predictor(self):
        return NEETCollegePredictor(CSV)

    def test_loads_data(self, predictor):
        assert len(predictor._df) > 0

    def test_large_dataset(self, predictor):
        """Dataset should have 3000+ rows after expansion."""
        assert len(predictor._df) > 3000

    def test_multiple_colleges(self, predictor):
        """Should have 100+ unique colleges."""
        colleges = set(r['college_name'] for r in predictor._df)
        assert len(colleges) > 100

    def test_multiple_states(self, predictor):
        """Should cover 20+ states."""
        states = set(r['state'] for r in predictor._df)
        assert len(states) > 20

    def test_has_new_columns(self, predictor):
        """Dataset should have city, mbbs_seats, nmc_ranking columns."""
        row = predictor._df[0]
        assert 'city' in row
        assert 'mbbs_seats' in row
        assert 'nmc_ranking' in row

    def test_predict_returns_list(self, predictor):
        results = predictor.predict(rank=50000, category='OBC', state='Maharashtra')
        assert isinstance(results, list)

    def test_all_results_within_cutoff(self, predictor):
        rank    = 20000
        results = predictor.predict(rank=rank, category='OBC')
        for r in results:
            assert r.closing_rank >= rank, \
                f'{r.college_name}: closing_rank {r.closing_rank} < student rank {rank}'

    def test_results_sorted_by_closing_rank(self, predictor):
        results = predictor.predict(rank=50000, category='SC')
        ranks   = [r.closing_rank for r in results]
        assert ranks == sorted(ranks)

    def test_top_n_respected(self, predictor):
        results = predictor.predict(rank=100000, category='OBC', top_n=3)
        assert len(results) <= 3

    def test_state_filter_only_returns_matching_or_aiq(self, predictor):
        results = predictor.predict(rank=50000, category='OBC', state='Maharashtra')
        for r in results:
            assert r.state.lower() == 'maharashtra' or r.quota == 'AIQ', \
                f'Unexpected state {r.state} with quota {r.quota}'

    def test_college_type_filter(self, predictor):
        """College type filtering is done via CounsellingStrategy, not predict().
        Just verify predict works with the basic filters."""
        results = predictor.predict(rank=5000, category='GEN')
        if results:
            # All results should have valid college types
            for r in results:
                assert r.college_type in ('GOVT', 'CENTRAL', 'PRIVATE', 'DEEMED')

    def test_empty_for_impossible_rank(self, predictor):
        results = predictor.predict(rank=1, category='GEN')
        assert isinstance(results, list)

    def test_predict_as_dicts_structure(self, predictor):
        results = predictor.predict_as_dicts(rank=60000, category='SC')
        if results:
            assert 'college_name' in results[0]
            assert 'closing_rank' in results[0]
            assert 'chance_label' in results[0]
            assert 'city' in results[0]
            assert 'mbbs_seats' in results[0]


# ── Counselling Strategy ──────────────────────────────────────────────────────

@pytest.mark.skipif(not CSV.exists(), reason='CSV dataset not found')
class TestCounsellingStrategyEngine:
    @pytest.fixture(scope='class')
    def engine(self):
        return CounsellingStrategyEngine(CSV)

    def test_build_strategy_returns_object(self, engine):
        s = engine.build_strategy(rank=20000, category='OBC', state='Maharashtra')
        assert s is not None

    def test_safe_colleges_have_closing_rank_gte_student_rank(self, engine):
        s = engine.build_strategy(rank=20000, category='OBC')
        for c in s.safe_colleges:
            assert c.closing_rank >= 20000

    def test_target_colleges_between_bounds(self, engine):
        rank    = 20000
        low     = rank / 1.5   # ~13333
        s       = engine.build_strategy(rank=rank, category='OBC')
        for c in s.target_colleges:
            assert low <= c.closing_rank < rank, \
                f'Target college {c.college} closing={c.closing_rank} out of range [{low}, {rank})'

    def test_dream_colleges_below_lower_bound(self, engine):
        rank = 20000
        low  = rank / 1.5
        s    = engine.build_strategy(rank=rank, category='OBC')
        for c in s.dream_colleges:
            assert c.closing_rank < low

    def test_flat_list_format(self, engine):
        s    = engine.build_strategy(rank=50000, category='GEN')
        flat = s.to_flat_list()
        for item in flat:
            assert 'college'  in item
            assert 'category' in item
            assert item['category'] in ('Dream', 'Target', 'Safe')

    def test_all_tiers_not_overlapping(self, engine):
        """Same college+quota should not appear in multiple tiers."""
        s = engine.build_strategy(rank=20000, category='OBC')
        safe_keys   = {(c.college, c.quota) for c in s.safe_colleges}
        target_keys = {(c.college, c.quota) for c in s.target_colleges}
        dream_keys  = {(c.college, c.quota) for c in s.dream_colleges}
        assert safe_keys.isdisjoint(target_keys), 'Safe and Target overlap'
        assert safe_keys.isdisjoint(dream_keys),  'Safe and Dream overlap'
        assert target_keys.isdisjoint(dream_keys),'Target and Dream overlap'

    def test_college_type_filter_in_strategy(self, engine):
        s = engine.build_strategy(rank=30000, category='GEN', college_type='GOVT')
        for c in s.all_colleges:
            assert c.college_type == 'GOVT'

    def test_strategy_entries_have_new_fields(self, engine):
        s = engine.build_strategy(rank=30000, category='GEN')
        if s.all_colleges:
            c = s.all_colleges[0]
            assert hasattr(c, 'city')
            assert hasattr(c, 'mbbs_seats')
            assert hasattr(c, 'nmc_ranking')


# ── Scorer ────────────────────────────────────────────────────────────────────

@pytest.mark.skipif(not CSV.exists(), reason='CSV dataset not found')
class TestCollegeScorer:
    @pytest.fixture(scope='class')
    def pipeline(self):
        return ScoredPredictionPipeline(CSV)

    def test_scores_between_0_and_100(self, pipeline):
        results = pipeline.run(rank=30000, category='OBC', state='Maharashtra')
        for c in results:
            assert 0 <= c.score.total_score <= 100, \
                f'{c.college}: score {c.score.total_score} out of [0,100]'

    def test_component_scores_dont_exceed_max(self, pipeline):
        results = pipeline.run(rank=30000, category='OBC')
        for c in results:
            b = c.score
            assert b.rank_proximity_score  <= 60
            assert b.state_match_score     <= 25
            assert b.category_bonus_score  <= 15

    def test_same_state_sq_gets_full_state_score(self, pipeline):
        """A college in same state as student with SQ quota must get 25/25 state score."""
        results = pipeline.run(rank=30000, category='OBC', state='Maharashtra', quota='SQ')
        for c in results:
            if c.state == 'Maharashtra' and c.quota == 'SQ':
                assert c.score.state_match_score == 25.0

    def test_sort_by_score_is_descending(self, pipeline):
        results = pipeline.run(rank=50000, category='OBC', sort_by='score')
        scores  = [c.score.total_score for c in results]
        assert scores == sorted(scores, reverse=True)

    def test_sort_by_closing_rank_is_ascending(self, pipeline):
        results = pipeline.run(rank=80000, category='OBC', sort_by='closing_rank')
        ranks   = [c.closing_rank for c in results]
        assert ranks == sorted(ranks)

    def test_display_line_format(self, pipeline):
        results = pipeline.run(rank=40000, category='SC')
        for c in results:
            assert '|' in c.display_line
            assert 'Score:' in c.display_line
            assert '%' in c.display_line

    def test_no_duplicate_college_quota_per_run(self, pipeline):
        """Same college+quota combo should not appear more than once."""
        results = pipeline.run(rank=50000, category='OBC')
        keys = [(c.college, c.quota) for c in results]
        assert len(keys) == len(set(keys)), 'Duplicate college+quota combos in results'

    def test_scored_college_has_new_fields(self, pipeline):
        results = pipeline.run(rank=30000, category='GEN')
        if results:
            c = results[0]
            assert hasattr(c, 'city')
            assert hasattr(c, 'mbbs_seats')
            assert hasattr(c, 'nmc_ranking')

    def test_college_type_filter_in_pipeline(self, pipeline):
        results = pipeline.run(rank=50000, category='GEN', college_type='CENTRAL')
        for c in results:
            assert c.college_type == 'CENTRAL'

    def test_more_results_with_large_dataset(self, pipeline):
        """With expanded dataset, we should get more results."""
        results = pipeline.run(rank=50000, category='GEN')
        assert len(results) > 5, f'Expected >5 results, got {len(results)}'
