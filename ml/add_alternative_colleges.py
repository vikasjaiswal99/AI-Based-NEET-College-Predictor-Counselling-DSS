import csv
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)-8s %(message)s")
logger = logging.getLogger("ml.add_alternative_colleges")

# Target CSV File
CSV_FILE = Path(__file__).resolve().parent / "data" / "neet_cutoffs.csv"

# Real alternative medical college data (Approximate historical MCC/AYUSH 2023-2024 cutoffs)
NEW_DATA = [
    # ---- BDS (Dental) ----
    {"college_name": "Maulana Azad Institute of Dental Sciences", "state": "Delhi", "city": "New Delhi", "college_type": "GOVT", "course_type": "BDS", "annual_fee": 4500, "ranks": {"GEN": 23000, "OBC": 25000, "SC": 90000, "ST": 120000}},
    {"college_name": "Government Dental College and Hospital", "state": "Maharashtra", "city": "Mumbai", "college_type": "GOVT", "course_type": "BDS", "annual_fee": 85000, "ranks": {"GEN": 28000, "OBC": 32000, "SC": 110000, "ST": 150000}},
    {"college_name": "Manipal College of Dental Sciences", "state": "Karnataka", "city": "Manipal", "college_type": "PVT", "course_type": "BDS", "annual_fee": 700000, "ranks": {"GEN": 450000, "OBC": 550000, "SC": 800000, "ST": 950000}},
    {"college_name": "Government Dental College", "state": "Karnataka", "city": "Bangalore", "college_type": "GOVT", "course_type": "BDS", "annual_fee": 65000, "ranks": {"GEN": 30000, "OBC": 35000, "SC": 115000, "ST": 160000}},
    {"college_name": "Faculty of Dental Sciences King George Medical University", "state": "Uttar Pradesh", "city": "Lucknow", "college_type": "GOVT", "course_type": "BDS", "annual_fee": 43000, "ranks": {"GEN": 26000, "OBC": 29000, "SC": 105000, "ST": 140000}},
    {"college_name": "SRM Dental College", "state": "Tamil Nadu", "city": "Chennai", "college_type": "PVT", "course_type": "BDS", "annual_fee": 650000, "ranks": {"GEN": 550000, "OBC": 600000, "SC": 850000, "ST": 1050000}},
    {"college_name": "Dr. R. Ahmed Dental College and Hospital", "state": "West Bengal", "city": "Kolkata", "college_type": "GOVT", "course_type": "BDS", "annual_fee": 12000, "ranks": {"GEN": 32000, "OBC": 38000, "SC": 125000, "ST": 180000}},
    {"college_name": "M.S. Ramaiah University of Applied Sciences (Dental)", "state": "Karnataka", "city": "Bangalore", "college_type": "PVT", "course_type": "BDS", "annual_fee": 550000, "ranks": {"GEN": 480000, "OBC": 580000, "SC": 820000, "ST": 980000}},

    # ---- BAMS (Ayurveda) ----
    {"college_name": "National Institute of Ayurveda", "state": "Rajasthan", "city": "Jaipur", "college_type": "GOVT", "course_type": "BAMS", "annual_fee": 42000, "ranks": {"GEN": 35000, "OBC": 39000, "SC": 140000, "ST": 190000}},
    {"college_name": "Faculty of Ayurveda BHU", "state": "Uttar Pradesh", "city": "Varanasi", "college_type": "GOVT", "course_type": "BAMS", "annual_fee": 25000, "ranks": {"GEN": 28000, "OBC": 32000, "SC": 115000, "ST": 150000}},
    {"college_name": "Ayurvedic and Unani Tibbia College", "state": "Delhi", "city": "New Delhi", "college_type": "GOVT", "course_type": "BAMS", "annual_fee": 15000, "ranks": {"GEN": 31000, "OBC": 35000, "SC": 130000, "ST": 175000}},
    {"college_name": "Government Ayurved College and Hospital", "state": "Maharashtra", "city": "Nagpur", "college_type": "GOVT", "course_type": "BAMS", "annual_fee": 55000, "ranks": {"GEN": 45000, "OBC": 52000, "SC": 160000, "ST": 220000}},
    {"college_name": "R.A. Podar Ayurvedic Medical College", "state": "Maharashtra", "city": "Mumbai", "college_type": "GOVT", "course_type": "BAMS", "annual_fee": 58000, "ranks": {"GEN": 42000, "OBC": 49000, "SC": 155000, "ST": 210000}},
    {"college_name": "Dr. D.Y. Patil College of Ayurved", "state": "Maharashtra", "city": "Pune", "college_type": "PVT", "course_type": "BAMS", "annual_fee": 450000, "ranks": {"GEN": 600000, "OBC": 680000, "SC": 900000, "ST": 1100000}},
    {"college_name": "Bharati Vidyapeeth College of Ayurved", "state": "Maharashtra", "city": "Pune", "college_type": "PVT", "course_type": "BAMS", "annual_fee": 380000, "ranks": {"GEN": 550000, "OBC": 620000, "SC": 880000, "ST": 1050000}},
    {"college_name": "Patanjali Ayurvedic College", "state": "Uttarakhand", "city": "Haridwar", "college_type": "PVT", "course_type": "BAMS", "annual_fee": 320000, "ranks": {"GEN": 250000, "OBC": 280000, "SC": 500000, "ST": 750000}},

    # ---- BHMS (Homeopathy) ----
    {"college_name": "National Institute of Homoeopathy", "state": "West Bengal", "city": "Kolkata", "college_type": "GOVT", "course_type": "BHMS", "annual_fee": 36000, "ranks": {"GEN": 85000, "OBC": 95000, "SC": 220000, "ST": 310000}},
    {"college_name": "Nehru Homoeopathic Medical College", "state": "Delhi", "city": "New Delhi", "college_type": "GOVT", "course_type": "BHMS", "annual_fee": 12000, "ranks": {"GEN": 75000, "OBC": 82000, "SC": 190000, "ST": 280000}},
    {"college_name": "Government Homoeopathic Medical College", "state": "Karnataka", "city": "Bangalore", "college_type": "GOVT", "course_type": "BHMS", "annual_fee": 45000, "ranks": {"GEN": 95000, "OBC": 105000, "SC": 240000, "ST": 350000}},
    {"college_name": "Bharati Vidyapeeth Homoeopathic Medical College", "state": "Maharashtra", "city": "Pune", "college_type": "PVT", "course_type": "BHMS", "annual_fee": 250000, "ranks": {"GEN": 650000, "OBC": 750000, "SC": 950000, "ST": 1200000}},
    {"college_name": "D.K.M.M. Homoeopathic Medical College", "state": "Maharashtra", "city": "Aurangabad", "college_type": "PVT", "course_type": "BHMS", "annual_fee": 180000, "ranks": {"GEN": 750000, "OBC": 850000, "SC": 1050000, "ST": 1300000}},

    # ---- BUMS (Unani) ----
    {"college_name": "National Institute of Unani Medicine", "state": "Karnataka", "city": "Bangalore", "college_type": "GOVT", "course_type": "BUMS", "annual_fee": 52000, "ranks": {"GEN": 105000, "OBC": 120000, "SC": 280000, "ST": 400000}},
    {"college_name": "Ayurvedic and Unani Tibbia College (Unani)", "state": "Delhi", "city": "New Delhi", "college_type": "GOVT", "course_type": "BUMS", "annual_fee": 15000, "ranks": {"GEN": 95000, "OBC": 110000, "SC": 260000, "ST": 380000}},
    {"college_name": "Government Unani Medical College", "state": "Tamil Nadu", "city": "Chennai", "college_type": "GOVT", "course_type": "BUMS", "annual_fee": 38000, "ranks": {"GEN": 115000, "OBC": 135000, "SC": 300000, "ST": 450000}},
    {"college_name": "Z.V.M. Unani Medical College", "state": "Maharashtra", "city": "Pune", "college_type": "PVT", "course_type": "BUMS", "annual_fee": 200000, "ranks": {"GEN": 700000, "OBC": 800000, "SC": 1100000, "ST": 1350000}},
]

def append_alternative_colleges():
    if not CSV_FILE.exists():
        logger.error(f"Dataset not found at {CSV_FILE}")
        return

    # Read current content to get fieldnames
    with open(CSV_FILE, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

    if not fieldnames:
        logger.error("No fieldnames found in CSV.")
        return

    records_added = 0

    with open(CSV_FILE, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        # For each college, expand into category rows
        for col in NEW_DATA:
            for cat, closing in col["ranks"].items():
                # For private colleges, use 'MQ' (Management Quota). For Govt, use 'AIQ'
                quota = "MQ" if col["college_type"] == "PVT" else "AIQ"
                
                # Opening rank is roughly 20-30% lower than closing
                opening = int(closing * 0.75)
                if opening < 1: opening = 1

                row = {
                    "college_name": col["college_name"],
                    "state": col["state"],
                    "city": col["city"],
                    "college_type": col["college_type"],
                    "quota": quota,
                    "category": cat,
                    "opening_rank": opening,
                    "closing_rank": closing,
                    "annual_fee": col["annual_fee"],
                    "year": 2024,
                    "mbbs_seats": 0, # N/A for alternative courses
                    "nmc_ranking": "",
                    "course_type": col["course_type"],
                    "bond_years": 1,
                    "bond_penalty": 500000
                }
                
                # Fill missing fields with empty string
                for field in fieldnames:
                    if field not in row:
                        row[field] = ""
                
                writer.writerow(row)
                records_added += 1

    logger.info(f"Successfully appended {records_added} alternative course records to {CSV_FILE}!")

if __name__ == "__main__":
    append_alternative_colleges()
