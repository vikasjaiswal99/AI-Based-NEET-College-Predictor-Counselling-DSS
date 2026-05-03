import os
import sys
import csv
import django
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.predictions.models import CollegeCutoff
import logging

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)-8s %(message)s")
logger = logging.getLogger("ml.migrate_to_sqlite")

def _to_int(value):
    if not value: return None
    s = str(value).strip()
    if not s: return None
    try: return int(float(s))
    except ValueError: return None

def _to_float(value):
    if not value: return None
    s = str(value).strip()
    if not s: return None
    try: return float(s)
    except ValueError: return None

def run():
    csv_path = BASE_DIR / "ml" / "data" / "neet_cutoffs.csv"
    if not csv_path.exists():
        logger.error(f"CSV not found at {csv_path}")
        return

    logger.info("Clearing existing records...")
    CollegeCutoff.objects.all().delete()

    batch = []
    batch_size = 5000

    logger.info("Reading CSV and inserting into SQLite...")
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            opening_rank = _to_int(raw.get("opening_rank"))
            closing_rank = _to_int(raw.get("closing_rank"))
            year = _to_int(raw.get("year"))

            if opening_rank is None or closing_rank is None:
                continue
            if opening_rank > closing_rank:
                continue

            annual_fee = _to_float(raw.get("annual_fee")) or 0.0
            mbbs_seats = _to_int(raw.get("mbbs_seats")) or 0
            
            nmc_str = raw.get("nmc_ranking")
            nmc_ranking = int(float(nmc_str)) if nmc_str and nmc_str != "0" else None
            
            bond_years = _to_int(raw.get("bond_years")) or 0
            bond_penalty = _to_float(raw.get("bond_penalty")) or 0.0

            college_name = (raw.get("college_name") or "").strip()
            if not college_name:
                continue

            obj = CollegeCutoff(
                college_name=college_name,
                state=(raw.get("state") or "").strip().title(),
                city=(raw.get("city") or "").strip().title(),
                college_type=(raw.get("college_type") or "").strip().upper(),
                quota=(raw.get("quota") or "").strip().upper(),
                category=(raw.get("category") or "").strip().upper(),
                opening_rank=opening_rank,
                closing_rank=closing_rank,
                annual_fee=annual_fee,
                year=year if year is not None else 0,
                mbbs_seats=mbbs_seats,
                nmc_ranking=nmc_ranking,
                course_type=(raw.get("course_type") or "MBBS").strip().upper(),
                bond_years=bond_years,
                bond_penalty=bond_penalty
            )
            batch.append(obj)

            if len(batch) >= batch_size:
                CollegeCutoff.objects.bulk_create(batch)
                logger.info(f"Inserted {batch_size} records...")
                batch.clear()

        # Insert remaining
        if batch:
            CollegeCutoff.objects.bulk_create(batch)
            logger.info(f"Inserted {len(batch)} records...")

    total = CollegeCutoff.objects.count()
    logger.info(f"Migration completed! Total records in SQLite: {total}")

if __name__ == "__main__":
    run()
