<<<<<<< HEAD
# AI-Based NEET College Predictor & Counselling DSS

###  

---

## Quick Start (5 commands)

```bash
git clone <repo>  &&  cd neet_predictor
python -m venv venv  &&  source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in secret key (SQLite DB is file-based)
python manage.py migrate
python manage.py runserver    # → http://127.0.0.1:8000
```

---

## Project Structure

```
neet_predictor/
│
├── config/                    # Django project config
│   ├── settings.py            # All settings (env-var driven)
│   ├── urls.py                # Root URL dispatcher
│   └── wsgi.py
│
├── apps/
│   ├── accounts/              # Custom User, StudentProfile, Login/Register
│   ├── colleges/              # College master data (stub — extend as needed)
│   ├── predictions/           # ML views, forms, models, URLs
│   └── counselling/           # Counselling schedules (stub)
│
├── ml/                        # ← Pure Python ML modules (no Django dependency)
│   ├── ml_model.py            # CSV predictor + StudentInput validation
│   ├── counselling_strategy.py# Dream/Target/Safe classifier
│   ├── college_scorer.py      # 100-pt scoring + full pipeline
│   └── data/
│       └── neet_cutoffs.csv   # Historical cutoff dataset (120+ rows, extend this)
│
├── templates/
│   ├── base.html              # Site nav, footer, messages
│   ├── predictions/
│   │   ├── predict.html       # Main predictor UI (form + results)
│   │   └── formula.html       # Scoring formula explainer
│   └── registration/
│       ├── login.html
│       └── register.html
│
├── tests/
│   └── test_ml_pipeline.py    # 24 unit tests — all pass
│
├── static/                    # CSS/JS/images (extend as needed)
├── logs/                      # Rotating log files (auto-created)
├── manage.py
├── requirements.txt
└── .env.example
```

---

## Key URLs

| URL                            | View                | Description                   |
| ------------------------------ | ------------------- | ----------------------------- |
| `/`                            | PredictView         | Main predictor form + results |
| `/formula/`                    | FormulaView         | Scoring formula explainer     |
| `/auth/login/`                 | LoginView           | Email/password login          |
| `/auth/register/`              | RegisterView        | Student signup                |
| `/auth/logout/`                | LogoutView          | POST to logout                |
| `/admin/`                      | Django Admin        | Full data management          |
| `/api/docs/`                   | Swagger UI          | Auto-generated API docs       |
| `/api/v1/auth/token/`          | TokenObtainPairView | JWT login                     |
| `/api/v1/predictions/predict/` | PredictionAPIView   | JSON prediction endpoint      |

---

## ML Pipeline Architecture

```
CSV File (neet_cutoffs.csv)
        │
        ▼
NEETCollegePredictor          ml/ml_model.py
  └─ loads + validates CSV
  └─ applies filters (category, rank window, state, quota)
  └─ returns CollegeRecommendation list
        │
        ▼
CounsellingStrategyEngine     ml/counselling_strategy.py
  └─ skips rank window filter (fetches ALL colleges)
  └─ assigns Dream / Target / Safe tier to each
  └─ splits into 3 buckets, caps per tier
        │
        ▼
ScoredPredictionPipeline      ml/college_scorer.py
  └─ CollegeScorer.score() for every StrategyEntry
  └─ Score = Rank Proximity(60) + State Match(25) + Category(15)
  └─ sorts by score / tier / closing_rank
  └─ returns list[ScoredCollege]
        │
        ▼
views.py _enrich()            apps/predictions/views.py
  └─ converts ScoredCollege → flat template dict
  └─ pre-formats: "₹42,000", "+2,000", "62.0%"
        │
        ▼
predict.html                  templates/predictions/predict.html
  └─ Bootstrap 5 + tier tabs + animated score bars
  └─ collapsible reasoning per college
```

---

## Scoring Formula

```
Total Score = A + B + C  (capped at 100)

A. Rank Proximity  (max 60 pts)
   Within cutoff:   min(closing/student, 3.0) / 3.0 × 60
   Outside cutoff:  (1 − gap_fraction) × 30  (Dream colleges)

B. State Match     (max 25 pts)
   Same state + SQ  → 25   Same state + AIQ → 15
   Diff state + AIQ → 10   Diff state + SQ  →  0

C. Category Bonus  (max 15 pts)
   Any match (base)      → 10
   Reserved + GOVT       → +5 (mandated reservations)
   GEN + PRIVATE/DEEMED  → +3 (less reservation competition)
```

---

## Database Setup (SQLite)

SQLite is file-based, so no external DB server is required. Django will create the DB file automatically.

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser
```

---

## Extending the Dataset

The CSV at `ml/data/neet_cutoffs.csv` has 120+ rows covering major colleges.
For production use, expand it with data from:

- **MCC Portal**: https://mcc.nic.in (All India Quota)
- **State authorities**: state-specific counselling result PDFs
- One row = one unique (college, state, quota, category, year) combination

Required CSV columns:

```
college_name, state, college_type, quota, category,
opening_rank, closing_rank, annual_fee, year
```

---

## Running Tests

```bash
# With pytest (after pip install pytest pytest-django):
pytest tests/test_ml_pipeline.py -v

# Without pytest (pure Python):
python tests/test_ml_pipeline.py
```

**24 tests covering:**

- StudentInput validation (rank, category, state, quota)
- Predictor filtering (cutoff window, state+AIQ logic)
- Tier classification (Safe/Target/Dream boundaries, no overlap)
- Scoring (0–100 bounds, component max, sort order)
- Output format (display_line, flat list, no duplicates)

---

## Environment Variables (.env)

| Variable            | Default                    | Description                                       |
| ------------------- | -------------------------- | ------------------------------------------------- |
| `DJANGO_SECRET_KEY` | _(required)_               | Django secret key                                 |
| `DEBUG`             | `True`                     | Set `False` in production                         |
| `ALLOWED_HOSTS`     | `localhost,127.0.0.1`      | Comma-separated hosts                             |
| `SQLITE_DB_PATH`    | `db.sqlite3`               | SQLite database file path (created automatically) |
| `ML_CSV_PATH`       | `ml/data/neet_cutoffs.csv` | Absolute path to CSV                              |

---

## Production Checklist

- [ ] Set `DEBUG=False` in `.env`
- [ ] Set a strong `DJANGO_SECRET_KEY` (50+ random chars)
- [ ] Set `ALLOWED_HOSTS` to your domain
- [ ] Run `python manage.py collectstatic`
- [ ] Use gunicorn: `gunicorn config.wsgi:application`
- [ ] Set up Nginx to serve `/static/` and proxy to gunicorn
- [ ] Replace sample CSV with full MCC dataset (5,000+ rows)
- [ ] Ensure `SQLITE_DB_PATH` points to a writable location (default `db.sqlite3` inside project)
- [ ] Set up log rotation for `logs/neet_predictor.log`

---

## Tech Stack

| Layer        | Technology                           |
| ------------ | ------------------------------------ |
| Framework    | Django 5.0.6                         |
| API          | Django REST Framework 3.15.2         |
| Auth         | SimpleJWT 5.3.1                      |
| Database     | PostgreSQL 14+                       |
| ML / Data    | pandas 2.2.2                         |
| Static files | WhiteNoise 6.7.0                     |
| Config       | python-decouple 3.8                  |
| Frontend     | Bootstrap 5.3 + Bootstrap Icons      |
| Fonts        | Syne (display) + DM Sans (body)      |
| API Docs     | drf-spectacular (Swagger UI + ReDoc) |
=======
# AI-Based-NEET-College-Predictor-Counselling-DSS
 AI-based NEET College Predictor helps students find suitable medical colleges using rank, marks, and category. It analyzes past cutoff data to give accurate predictions and counselling guidance, reducing confusion and helping students make better admission decisions easily.
>>>>>>> d84cdf2968f702c5be18c2ca27d0cbf0e37e708c
