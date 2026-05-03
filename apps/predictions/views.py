"""
apps/predictions/views.py
=========================
Django views wired to the ML scoring pipeline.
Pipeline is a module-level singleton — CSV loads once per worker.
"""
import logging
from pathlib import Path

from django.conf import settings
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

# ── ML pipeline (absolute import from ml package) ────────────────────────────
import sys
ML_DIR = Path(__file__).resolve().parent.parent.parent / 'ml'
if str(ML_DIR.parent) not in sys.path:
    sys.path.insert(0, str(ML_DIR.parent))

from ml.college_scorer import ScoredPredictionPipeline, ScoredCollege
from ml.counselling_strategy import Tier
from ml.trend_analyzer import TrendAnalyzer

from .forms import PredictionForm
from .models import PredictionSession

logger = logging.getLogger('apps.predictions')

# ── Singleton pipeline ────────────────────────────────────────────────────────
_CSV_PATH = Path(getattr(settings, 'ML_CSV_PATH',
                          ML_DIR / 'data' / 'neet_cutoffs.csv'))
try:
    _PIPELINE = ScoredPredictionPipeline(csv_path=_CSV_PATH)
    logger.info('ML pipeline loaded from %s', _CSV_PATH)
except FileNotFoundError:
    _PIPELINE = None
    logger.error('ML CSV not found at %s', _CSV_PATH)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _score_css(score: float) -> str:
    if score >= 80: return 'score-excellent'
    if score >= 60: return 'score-good'
    if score >= 40: return 'score-fair'
    return 'score-low'


def _enrich(c: ScoredCollege) -> dict:
    """Convert ScoredCollege → flat template-ready dict. All formatting here."""
    s   = c.score
    b   = s.to_dict()['breakdown']
    tier_val = c.tier.value if isinstance(c.tier, Tier) else str(c.tier)
    return {
        'college'               : c.college,
        'state'                 : c.state,
        'city'                  : c.city,
        'college_type'          : c.college_type,
        'quota'                 : c.quota,
        'category'              : c.category,
        'closing_rank'          : f'{c.closing_rank:,}',
        'closing_rank_raw'      : c.closing_rank,
        'annual_fee'            : f'₹{c.annual_fee:,.0f}',
        'annual_fee_raw'        : c.annual_fee,
        'mbbs_seats'            : c.mbbs_seats,
        'nmc_ranking'           : c.nmc_ranking,
        'course_type'           : c.course_type,
        'bond_years'            : c.bond_years,
        'bond_penalty'          : f'₹{c.bond_penalty:,.0f}',
        'tier'                  : tier_val,
        'rank_gap'              : c.rank_gap,
        'rank_gap_display'      : f'+{c.rank_gap:,}' if c.rank_gap >= 0 else f'{c.rank_gap:,}',
        'admission_probability' : f'{c.admission_probability * 100:.0f}%',
        'advice'                : c.advice,
        'display_line'          : c.display_line,
        'score_total'           : s.total_score,
        'score_formatted'       : s.formatted,
        'score_label'           : s.score_label,
        'score_css'             : _score_css(s.total_score),
        'score_bar_width'       : int(s.total_score),
        'breakdown': {
            'rank'    : {**b['rank_proximity'],
                         'pct': int(b['rank_proximity']['score'] / 60 * 100)},
            'state'   : {**b['state_match'],
                         'pct': int(b['state_match']['score'] / 25 * 100)},
            'category': {**b['category_bonus'],
                         'pct': int(b['category_bonus']['score'] / 15 * 100)},
        },
    }


# ── Views ─────────────────────────────────────────────────────────────────────

class PredictView(LoginRequiredMixin, View):
    """GET → form | POST → run pipeline → results."""
    template_name = 'predictions/predict.html'
    login_url     = '/auth/login/'

    def get(self, request: HttpRequest) -> HttpResponse:
        # Pre-fill form from student profile if available
        initial = {}
        if hasattr(request.user, 'student_profile'):
            p = request.user.student_profile
            if p.neet_rank:   initial['rank']     = p.neet_rank
            if p.category:    initial['category'] = p.category
            if p.state_of_domicile: initial['state'] = p.state_of_domicile
        return render(request, self.template_name, {'form': PredictionForm(initial=initial)})

    def post(self, request: HttpRequest) -> HttpResponse:
        form    = PredictionForm(request.POST)
        context = {'form': form}

        if not form.is_valid():
            return render(request, self.template_name, context)

        if _PIPELINE is None:
            messages.error(request, 'Prediction dataset not available. Contact support.')
            return render(request, self.template_name, context)

        kwargs  = form.to_pipeline_kwargs()
        sort_by = kwargs.pop('sort_by', 'score')
        college_type = kwargs.pop('college_type', None)
        budget  = form.cleaned_data.get('budget')  # may be None

        try:
            results = _PIPELINE.run(**kwargs, sort_by=sort_by, college_type=college_type)
        except ValueError as exc:
            messages.error(request, f'Input error: {exc}')
            return render(request, self.template_name, context)
        except Exception as exc:
            logger.exception('Prediction error: %s', exc)
            messages.error(request, 'An unexpected error occurred. Please try again.')
            return render(request, self.template_name, context)

        if not results:
            messages.warning(request,
                f'No colleges found for Rank {kwargs["rank"]:,} · {kwargs["category"]} · '
                f'{kwargs.get("state") or "All States"}. Try broadening your search.')
            return render(request, self.template_name, context)

        enriched = [_enrich(c) for c in results]

        # ── Admission probability per college ──
        for e in enriched:
            score = e['score_total']
            tier = e['tier'].lower()
            if tier == 'safe':
                e['probability'] = min(95, int(60 + score * 0.35))
            elif tier == 'target':
                e['probability'] = min(75, int(30 + score * 0.45))
            else:
                e['probability'] = max(5, int(score * 0.35))

        # ── Budget filtering ──
        if budget:
            budget_results = [e for e in enriched if float(e['annual_fee_raw']) <= budget]
        else:
            budget_results = enriched

        safe   = [e for e in enriched if e['tier'].lower() == 'safe']
        target = [e for e in enriched if e['tier'].lower() == 'target']
        dream  = [e for e in enriched if e['tier'].lower() == 'dream']

        top_score = max(e['score_total'] for e in enriched)
        avg_score = sum(e['score_total'] for e in enriched) / len(enriched)

        # ── Smart Recommendations (best ROI) ──
        smart_picks = sorted(enriched, key=lambda e: (
            -e['probability'],
            float(e['annual_fee_raw']),
            -e['score_total']
        ))[:5]

        # ── AI Choice Filling Strategy ──
        choice_dream  = sorted(dream, key=lambda e: -e['score_total'])[:5]
        choice_target = sorted(target, key=lambda e: -e['probability'])[:7]
        choice_safe   = sorted(safe, key=lambda e: -e['probability'])[:5]
        if budget:
            choice_budget = sorted(
                [e for e in enriched if float(e['annual_fee_raw']) <= budget],
                key=lambda e: -e['probability']
            )[:5]
        else:
            choice_budget = []

        # ── What-If Analysis ──
        student_rank = kwargs['rank']
        whatif = {}
        for delta_label, factor in [('-20 marks', 1.25), ('+20 marks', 0.80)]:
            wi_rank = max(1, int(student_rank * factor))
            try:
                wi_results = _PIPELINE.run(
                    rank=wi_rank, category=kwargs['category'],
                    state=kwargs.get('state'), quota=kwargs.get('quota'),
                    sort_by='score', college_type=college_type,
                )
                wi_enriched = [_enrich(c) for c in wi_results]
                whatif[delta_label] = {
                    'rank': f'{wi_rank:,}',
                    'total': len(wi_enriched),
                    'safe': sum(1 for e in wi_enriched if e['tier'].lower() == 'safe'),
                    'target': sum(1 for e in wi_enriched if e['tier'].lower() == 'target'),
                    'dream': sum(1 for e in wi_enriched if e['tier'].lower() == 'dream'),
                }
            except Exception:
                whatif[delta_label] = {'rank': f'{wi_rank:,}', 'total': 0, 'safe': 0, 'target': 0, 'dream': 0}

        # ── Smart Alerts & Final Recommendation ──
        smart_alerts = []
        if not safe:
            smart_alerts.append("No safe options identified. Consider adding backup colleges to mitigate risk.")
        if len(dream) > (len(target) + len(safe)) and len(safe) < 3:
            smart_alerts.append("High risk of not securing a seat if only dream options are chosen.")
        if budget and not budget_results:
            smart_alerts.append("No colleges found within your specified budget. Consider education loans or expanding your financial limit.")
        elif budget and len(budget_results) < 5:
            smart_alerts.append(f"Only {len(budget_results)} colleges fit your budget, which limits your options.")

        final_recommendation = {}
        if safe:
            best_safe = max(safe, key=lambda e: e['score_total'])
            final_recommendation['best_option'] = best_safe['college']
            final_recommendation['alternatives'] = [c['college'] for c in sorted(safe, key=lambda e: e['score_total'], reverse=True)[1:3]]
            final_recommendation['risk_level'] = "LOW" if len(safe) >= 5 else "MEDIUM"
        elif target:
            best_target = max(target, key=lambda e: e['score_total'])
            final_recommendation['best_option'] = best_target['college']
            final_recommendation['alternatives'] = [c['college'] for c in sorted(target, key=lambda e: e['score_total'], reverse=True)[1:3]]
            final_recommendation['risk_level'] = "MEDIUM" if len(target) >= 5 else "HIGH"
        else:
            final_recommendation['best_option'] = "None identified"
            final_recommendation['alternatives'] = []
            final_recommendation['risk_level'] = "HIGH"

        # Save prediction session
        try:
            PredictionSession.objects.create(
                user=request.user,
                neet_rank=kwargs['rank'],
                neet_score=form.cleaned_data.get('neet_score'),
                category=kwargs['category'],
                state=kwargs.get('state') or '',
                quota=kwargs.get('quota') or '',
                total_results=len(enriched),
            )
        except Exception:
            pass  # Non-critical

        context.update({
            'results'        : enriched,
            'safe_colleges'  : safe,
            'target_colleges': target,
            'dream_colleges' : dream,
            'total'          : len(enriched),
            'safe_count'     : len(safe),
            'target_count'   : len(target),
            'dream_count'    : len(dream),
            'top_score'      : f'{top_score:.1f}',
            'avg_score'      : f'{avg_score:.1f}',
            'student_rank'   : f'{kwargs["rank"]:,}',
            'student_cat'    : kwargs['category'],
            'student_state'  : kwargs.get('state') or 'All States',
            'student_course' : kwargs.get('course') or 'MBBS',
            'sort_by'        : sort_by,
            'budget'         : budget,
            'budget_count'   : len(budget_results) if budget else None,
            'smart_picks'    : smart_picks,
            'choice_dream'   : choice_dream,
            'choice_target'  : choice_target,
            'choice_safe'    : choice_safe,
            'choice_budget'  : choice_budget,
            'whatif'         : whatif,
            'smart_alerts'   : smart_alerts,
            'final_rec'      : final_recommendation,
        })
        return render(request, self.template_name, context)


class FormulaView(View):
    """Scoring formula explainer — public page."""
    template_name = 'predictions/formula.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        formula = [
            {
                'component'  : 'Rank Proximity',
                'weight'     : 60, 'icon': '📊',
                'description': ('Measures how comfortably your rank fits the college\'s '
                                'historical cutoff. A college whose closing rank is 3× '
                                'yours earns full marks. Dream colleges get partial credit.'),
                'rules': [
                    ('Within cutoff',         '(closing_rank / student_rank) ÷ 3.0 × 60', 'Up to 60 pts'),
                    ('Outside cutoff (Dream)', '(1 − gap_fraction) × 30',                  'Up to 30 pts'),
                ],
            },
            {
                'component'  : 'State Match',
                'weight'     : 25, 'icon': '🗺️',
                'description': ('Rewards applying to your home state. 85% of govt seats '
                                'are State Quota (SQ) — exclusively for domicile students.'),
                'rules': [
                    ('Same state + SQ quota',  'Full state advantage',     '25 pts'),
                    ('Same state + AIQ quota', 'Partial advantage',        '15 pts'),
                    ('Out-of-state + AIQ',     'Neutral pan-India',        '10 pts'),
                    ('Out-of-state + SQ',      'SQ unavailable',           '0 pts'),
                ],
            },
            {
                'component'  : 'Category Bonus',
                'weight'     : 15, 'icon': '🏷️',
                'description': ('Rewards structural reservation advantages. All results '
                                'are already category-filtered (10 base pts guaranteed).'),
                'rules': [
                    ('Any match (base)',        'Always given',                  '10 pts'),
                    ('Reserved + GOVT college', 'Mandated seat reservations',    '+5 pts'),
                    ('GEN + PRIVATE/DEEMED',    'Less reservation competition',  '+3 pts'),
                ],
            },
        ]
        return render(request, self.template_name, {'formula': formula})


class ScholarshipView(View):
    """Scholarship guidelines & suggestions — public page."""
    template_name = 'predictions/scholarships.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, self.template_name)


class PredictionHistoryView(LoginRequiredMixin, View):
    """Show past prediction sessions for the logged-in user."""
    template_name = 'predictions/history.html'
    login_url     = '/auth/login/'

    def get(self, request: HttpRequest) -> HttpResponse:
        sessions = PredictionSession.objects.filter(user=request.user).order_by('-created_at')[:50]
        return render(request, self.template_name, {'sessions': sessions})


class CollegeExplorerView(View):
    """Browse all colleges in the dataset — public page."""
    template_name = 'predictions/colleges.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        if _PIPELINE is None:
            return render(request, self.template_name, {'colleges': []})

        # Get unique colleges from the raw data
        raw = _PIPELINE._engine._df
        seen = set()
        colleges = []
        for r in raw:
            name = r['college_name']
            if name in seen:
                continue
            seen.add(name)
            colleges.append({
                'name'        : name,
                'state'       : r['state'],
                'city'        : r.get('city', ''),
                'college_type': r['college_type'],
                'annual_fee'  : f"₹{r['annual_fee']:,.0f}",
                'annual_fee_raw': r['annual_fee'],
                'mbbs_seats'  : r.get('mbbs_seats', 0),
                'nmc_ranking' : r.get('nmc_ranking', 0),
            })

        # Apply search/filter from GET params
        q = request.GET.get('q', '').strip().lower()
        state_filter = request.GET.get('state', '')
        type_filter = request.GET.get('type', '')

        if q:
            colleges = [c for c in colleges if q in c['name'].lower() or q in c['city'].lower()]
        if state_filter:
            colleges = [c for c in colleges if c['state'] == state_filter]
        if type_filter:
            colleges = [c for c in colleges if c['college_type'] == type_filter]

        # Sort by NMC ranking (ranked first), then alphabetically
        colleges.sort(key=lambda c: (0 if c['nmc_ranking'] and c['nmc_ranking'] > 0 else 1, c['nmc_ranking'] or 999, c['name']))

        # Get filter options
        all_states = sorted(set(c['state'] for c in colleges if c['state']))
        all_types = sorted(set(c['college_type'] for c in colleges))

        from .forms import STATE_CHOICES
        return render(request, self.template_name, {
            'colleges': colleges,
            'total': len(colleges),
            'query': q,
            'state_filter': state_filter,
            'type_filter': type_filter,
            'states': STATE_CHOICES[1:],  # Remove 'All States' option
            'types': all_types,
        })


class PredictionAPIView(LoginRequiredMixin, View):
    """JSON API endpoint — returns prediction results as JSON."""
    login_url = '/auth/login/'

    def post(self, request: HttpRequest) -> JsonResponse:
        form = PredictionForm(request.POST)
        if not form.is_valid():
            return JsonResponse({'error': form.errors}, status=400)
        if _PIPELINE is None:
            return JsonResponse({'error': 'Dataset unavailable.'}, status=503)
        kwargs  = form.to_pipeline_kwargs()
        sort_by = kwargs.pop('sort_by', 'score')
        college_type = kwargs.pop('college_type', None)
        try:
            results = _PIPELINE.run(**kwargs, sort_by=sort_by, college_type=college_type)
            return JsonResponse({'results': [c.to_dict() for c in results], 'total': len(results)})
        except Exception as exc:
            return JsonResponse({'error': str(exc)}, status=500)


class ExportPDFView(LoginRequiredMixin, View):
    """Generate PDF report from prediction parameters stored in session."""
    login_url = '/auth/login/'

    def post(self, request: HttpRequest) -> HttpResponse:
        form = PredictionForm(request.POST)
        if not form.is_valid() or _PIPELINE is None:
            messages.error(request, 'Cannot generate PDF — invalid input.')
            return render(request, 'predictions/predict.html', {'form': form})

        kwargs = form.to_pipeline_kwargs()
        sort_by = kwargs.pop('sort_by', 'score')
        college_type = kwargs.pop('college_type', None)

        try:
            results = _PIPELINE.run(**kwargs, sort_by=sort_by, college_type=college_type)
        except Exception:
            messages.error(request, 'Error generating prediction.')
            return render(request, 'predictions/predict.html', {'form': form})

        if not results:
            messages.warning(request, 'No results to export.')
            return render(request, 'predictions/predict.html', {'form': form})

        enriched = [_enrich(c) for c in results]
        safe_count = sum(1 for e in enriched if e['tier'].lower() == 'safe')
        target_count = sum(1 for e in enriched if e['tier'].lower() == 'target')
        dream_count = sum(1 for e in enriched if e['tier'].lower() == 'dream')

        from .pdf_export import generate_prediction_pdf
        buffer = generate_prediction_pdf(
            student_rank=kwargs['rank'],
            student_category=kwargs['category'],
            student_state=kwargs.get('state') or 'All States',
            student_course=kwargs.get('course') or 'MBBS',
            results=enriched,
            safe_count=safe_count,
            target_count=target_count,
            dream_count=dream_count,
        )

        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="NEET_Prediction_Rank{kwargs["rank"]}.pdf"'
        )
        return response


class CompareView(LoginRequiredMixin, View):
    """Compare 2-3 colleges side by side."""
    template_name = 'predictions/compare.html'
    login_url = '/auth/login/'

    def get(self, request: HttpRequest) -> HttpResponse:
        names = request.GET.getlist('c')
        if not names or _PIPELINE is None:
            return render(request, self.template_name, {'colleges': [], 'available': _get_college_names()})

        # Look up colleges from raw data
        raw = _PIPELINE._engine._df
        colleges = []
        for name in names[:3]:  # Max 3
            rows = [r for r in raw if r['college_name'] == name]
            if not rows:
                continue
            # Get the most recent GEN/AIQ row
            gen_aiq = [r for r in rows if r['category'] == 'GEN' and r['quota'] == 'AIQ']
            if not gen_aiq:
                gen_aiq = [r for r in rows if r['category'] == 'GEN']
            if not gen_aiq:
                gen_aiq = rows
            gen_aiq.sort(key=lambda r: int(r['year']), reverse=True)
            latest = gen_aiq[0]

            # Trend
            analyzer = TrendAnalyzer(raw)
            trend = analyzer.get_trend(name, 'GEN', latest.get('quota', 'AIQ'))

            colleges.append({
                'name': latest['college_name'],
                'state': latest['state'],
                'city': latest.get('city', ''),
                'college_type': latest['college_type'],
                'annual_fee': f"₹{float(latest['annual_fee']):,.0f}",
                'annual_fee_raw': float(latest['annual_fee']),
                'mbbs_seats': int(latest.get('mbbs_seats', 0)),
                'nmc_ranking': int(latest.get('nmc_ranking') or 0) if latest.get('nmc_ranking') is not None else None,
                'course_type': latest.get('course_type', 'MBBS'),
                'bond_years': int(latest.get('bond_years') or 0),
                'bond_penalty': f"₹{float(latest.get('bond_penalty') or 0):,.0f}",
                'gen_closing_rank': f"{int(latest['closing_rank']):,}",
                'year': latest['year'],
                'trend': trend.direction if trend else 'N/A',
                'trend_icon': trend.direction_icon if trend else '—',
            })

        return render(request, self.template_name, {
            'colleges': colleges,
            'available': _get_college_names(),
            'selected': names,
        })


class TrendView(View):
    """Cutoff trend analysis — public page."""
    template_name = 'predictions/trends.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        if _PIPELINE is None:
            return render(request, self.template_name, {'trends': []})

        raw = _PIPELINE._engine._df
        analyzer = TrendAnalyzer(raw)

        category = request.GET.get('category', 'GEN').upper()
        quota = request.GET.get('quota', 'AIQ').upper()

        all_trends = analyzer.get_all_trends(category, quota)
        tightening = analyzer.get_tightening_colleges(category, quota, top_n=10)
        easing = analyzer.get_easing_colleges(category, quota, top_n=10)

        return render(request, self.template_name, {
            'all_trends': [t.to_dict() for t in all_trends],
            'tightening': [t.to_dict() for t in tightening],
            'easing': [t.to_dict() for t in easing],
            'total': len(all_trends),
            'category': category,
            'quota': quota,
        })


import json
from django.http import JsonResponse
from ml.chatbot_engine import CounselingChatbot
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class AIChatbotView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            query = data.get('query', '')
            context = data.get('context', {})
            
            chatbot = CounselingChatbot(context)
            response = chatbot.get_response(query)
            
            return JsonResponse({'status': 'success', 'response': response})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)



def _get_college_names() -> list[str]:
    """Get sorted list of unique college names from the pipeline."""
    if _PIPELINE is None:
        return []
    raw = _PIPELINE._engine._df
    return sorted(set(r['college_name'] for r in raw))

class AboutView(View):
    template_name = 'predictions/about.html'
    def get(self, request):
        return render(request, self.template_name)
