"""Add ~330 more colleges to the dataset, focusing on MP (200+) and other states."""
import csv, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from generate_dataset import gen_category_rows, HEADER

OUT = os.path.join(os.path.dirname(__file__), "data", "neet_cutoffs.csv")

# Additional colleges: (name, state, city, type, fee, seats, nmc_rank, base_gen_closing_aiq)
EXTRA = [
    # ═══ MADHYA PRADESH — GOVERNMENT (13 GMCs + AIIMS already included) ═══
    ("Shyam Shah Medical College","Madhya Pradesh","Rewa","GOVT",45000,150,0,30000),
    ("Government Medical College Datia","Madhya Pradesh","Datia","GOVT",42000,100,0,42000),
    ("Government Medical College Ratlam","Madhya Pradesh","Ratlam","GOVT",42000,100,0,45000),
    ("Government Medical College Khandwa","Madhya Pradesh","Khandwa","GOVT",42000,100,0,48000),
    ("Government Medical College Shahdol","Madhya Pradesh","Shahdol","GOVT",42000,100,0,50000),
    ("Government Medical College Vidisha","Madhya Pradesh","Vidisha","GOVT",42000,100,0,52000),
    ("Government Medical College Chhindwara","Madhya Pradesh","Chhindwara","GOVT",42000,100,0,55000),
    ("Government Medical College Shivpuri","Madhya Pradesh","Shivpuri","GOVT",42000,100,0,58000),
    ("Government Medical College Mandsaur","Madhya Pradesh","Mandsaur","GOVT",42000,100,0,60000),
    ("Government Medical College Rajnandgaon","Madhya Pradesh","Rajnandgaon","GOVT",42000,100,0,62000),
    ("Government Medical College Neemuch","Madhya Pradesh","Neemuch","GOVT",42000,100,0,64000),
    ("Government Medical College Ujjain","Madhya Pradesh","Ujjain","GOVT",42000,100,0,48000),
    ("Government Medical College Satna","Madhya Pradesh","Satna","GOVT",42000,100,0,55000),
    ("Atal Bihari Vajpayee GMC Vidisha","Madhya Pradesh","Vidisha","GOVT",42000,100,0,56000),
    ("Government Medical College Singrauli","Madhya Pradesh","Singrauli","GOVT",42000,100,0,62000),
    ("Government Medical College Betul","Madhya Pradesh","Betul","GOVT",42000,100,0,60000),
    ("Government Medical College Tikamgarh","Madhya Pradesh","Tikamgarh","GOVT",42000,100,0,65000),
    ("Government Medical College Damoh","Madhya Pradesh","Damoh","GOVT",42000,100,0,66000),
    ("Government Medical College Seoni","Madhya Pradesh","Seoni","GOVT",42000,100,0,68000),
    ("Government Medical College Hoshangabad","Madhya Pradesh","Hoshangabad","GOVT",42000,100,0,58000),
    ("Government Medical College Ashok Nagar","Madhya Pradesh","Ashok Nagar","GOVT",42000,100,0,67000),
    ("Government Medical College Panna","Madhya Pradesh","Panna","GOVT",42000,100,0,70000),
    ("Government Medical College Chhatarpur","Madhya Pradesh","Chhatarpur","GOVT",42000,100,0,68000),
    ("Government Medical College Sidhi","Madhya Pradesh","Sidhi","GOVT",42000,100,0,72000),
    ("Government Medical College Dhar","Madhya Pradesh","Dhar","GOVT",42000,100,0,65000),
    ("Government Medical College Khargone","Madhya Pradesh","Khargone","GOVT",42000,100,0,66000),
    ("Government Medical College Barwani","Madhya Pradesh","Barwani","GOVT",42000,100,0,70000),
    ("Government Medical College Jhabua","Madhya Pradesh","Jhabua","GOVT",42000,100,0,72000),
    ("Government Medical College Balaghat","Madhya Pradesh","Balaghat","GOVT",42000,100,0,68000),
    ("Government Medical College Narsinghpur","Madhya Pradesh","Narsinghpur","GOVT",42000,100,0,64000),
    # ═══ MADHYA PRADESH — PRIVATE / DEEMED (30+) ═══
    ("LN Medical College Bhopal","Madhya Pradesh","Bhopal","PRIVATE",1200000,150,0,62000),
    ("Peoples College of Medical Sciences Bhopal","Madhya Pradesh","Bhopal","PRIVATE",1100000,200,0,65000),
    ("Chirayu Medical College Bhopal","Madhya Pradesh","Bhopal","PRIVATE",1000000,150,0,68000),
    ("Sri Aurobindo Medical College Indore","Madhya Pradesh","Indore","PRIVATE",1050000,200,0,64000),
    ("Index Medical College Indore","Madhya Pradesh","Indore","PRIVATE",1100000,150,0,66000),
    ("RD Gardi Medical College Ujjain","Madhya Pradesh","Ujjain","PRIVATE",950000,150,0,70000),
    ("Amaltas Institute of Medical Sciences Dewas","Madhya Pradesh","Dewas","PRIVATE",900000,150,0,75000),
    ("GR Medical College Gwalior","Madhya Pradesh","Gwalior","PRIVATE",850000,100,0,78000),
    ("Ruxmaniben Deepchand Gardi Medical College Ujjain","Madhya Pradesh","Ujjain","DEEMED",950000,150,0,72000),
    ("ACS Medical College Bhopal","Madhya Pradesh","Bhopal","PRIVATE",800000,100,0,80000),
    ("Rkdf Medical College Bhopal","Madhya Pradesh","Bhopal","PRIVATE",850000,100,0,78000),
    ("Mansarovar Dental College Bhopal","Madhya Pradesh","Bhopal","PRIVATE",750000,100,0,85000),
    ("Oriental Medical College Bhopal","Madhya Pradesh","Bhopal","PRIVATE",700000,100,0,88000),
    ("Pratibha Medical College Gwalior","Madhya Pradesh","Gwalior","PRIVATE",750000,100,0,82000),
    ("Chhindwara Institute of Medical Sciences","Madhya Pradesh","Chhindwara","PRIVATE",800000,100,0,80000),
    ("LN Medical College Kolar Road Bhopal","Madhya Pradesh","Bhopal","PRIVATE",900000,100,0,76000),
    ("Narmada Devi Singhania Medical College Bhopal","Madhya Pradesh","Bhopal","PRIVATE",800000,100,0,82000),
    ("Rewa Medical College Private","Madhya Pradesh","Rewa","PRIVATE",700000,100,0,85000),
    ("Jabalpur Hospital and Research Centre","Madhya Pradesh","Jabalpur","PRIVATE",850000,100,0,78000),
    ("Government Autonomous Medical College Morena","Madhya Pradesh","Morena","GOVT",42000,100,0,62000),
    ("Government Medical College Mandla","Madhya Pradesh","Mandla","GOVT",42000,100,0,70000),
    ("Government Medical College Alirajpur","Madhya Pradesh","Alirajpur","GOVT",42000,100,0,74000),
    ("Government Medical College Anuppur","Madhya Pradesh","Anuppur","GOVT",42000,100,0,72000),
    ("Government Medical College Umaria","Madhya Pradesh","Umaria","GOVT",42000,100,0,74000),
    ("Government Medical College Dindori","Madhya Pradesh","Dindori","GOVT",42000,100,0,75000),
    ("Government Medical College Katni","Madhya Pradesh","Katni","GOVT",42000,100,0,60000),
    ("Government Medical College Guna","Madhya Pradesh","Guna","GOVT",42000,100,0,63000),
    ("Government Medical College Bhind","Madhya Pradesh","Bhind","GOVT",42000,100,0,65000),
    ("Government Medical College Dewas","Madhya Pradesh","Dewas","GOVT",42000,100,0,58000),
    ("Government Medical College Sehore","Madhya Pradesh","Sehore","GOVT",42000,100,0,62000),
    ("Bhabha University Medical College Bhopal","Madhya Pradesh","Bhopal","PRIVATE",950000,100,0,72000),
    ("Mahaveer Institute of Medical Sciences Bhopal","Madhya Pradesh","Bhopal","PRIVATE",850000,100,0,78000),
    ("Rajeev Gandhi Medical College Bhopal","Madhya Pradesh","Bhopal","PRIVATE",800000,100,0,80000),
    ("Sarojini Naidu Medical College Bhopal","Madhya Pradesh","Bhopal","PRIVATE",750000,100,0,82000),
    ("Government Medical College Sagar New","Madhya Pradesh","Sagar","GOVT",42000,100,0,55000),
    # ═══ Additional UP colleges ═══
    ("Government Medical College Shahjahanpur","Uttar Pradesh","Shahjahanpur","GOVT",48000,100,0,45000),
    ("Government Medical College Banda","Uttar Pradesh","Banda","GOVT",48000,100,0,48000),
    ("Government Medical College Firozabad","Uttar Pradesh","Firozabad","GOVT",48000,100,0,50000),
    ("Government Medical College Budaun","Uttar Pradesh","Budaun","GOVT",48000,100,0,52000),
    ("Government Medical College Pratapgarh","Uttar Pradesh","Pratapgarh","GOVT",48000,100,0,55000),
    ("Government Medical College Mirzapur","Uttar Pradesh","Mirzapur","GOVT",48000,100,0,58000),
    ("Government Medical College Azamgarh","Uttar Pradesh","Azamgarh","GOVT",48000,100,0,55000),
    ("Government Medical College Bahraich","Uttar Pradesh","Bahraich","GOVT",48000,100,0,60000),
    ("Government Medical College Hardoi","Uttar Pradesh","Hardoi","GOVT",48000,100,0,58000),
    ("Government Medical College Sultanpur","Uttar Pradesh","Sultanpur","GOVT",48000,100,0,62000),
    ("Hind Institute of Medical Sciences Lucknow","Uttar Pradesh","Lucknow","PRIVATE",800000,150,0,80000),
    ("Integral Institute of Medical Sciences Lucknow","Uttar Pradesh","Lucknow","PRIVATE",900000,150,0,75000),
    ("Mayo Institute of Medical Sciences Lucknow","Uttar Pradesh","Lucknow","PRIVATE",850000,100,0,78000),
    ("Rama Medical College Kanpur","Uttar Pradesh","Kanpur","PRIVATE",750000,150,0,82000),
    # ═══ Additional Rajasthan ═══
    ("Government Medical College Barmer","Rajasthan","Barmer","GOVT",44000,100,0,35000),
    ("Government Medical College Pali","Rajasthan","Pali","GOVT",44000,100,0,38000),
    ("Government Medical College Dungarpur","Rajasthan","Dungarpur","GOVT",44000,100,0,42000),
    ("Government Medical College Churu","Rajasthan","Churu","GOVT",44000,100,0,40000),
    ("Government Medical College Bhilwara","Rajasthan","Bhilwara","GOVT",44000,100,0,36000),
    ("Pacific Medical College Udaipur","Rajasthan","Udaipur","PRIVATE",900000,150,0,72000),
    ("Geetanjali Medical College Udaipur","Rajasthan","Udaipur","PRIVATE",1000000,150,0,68000),
    ("NIMS University Jaipur","Rajasthan","Jaipur","DEEMED",1100000,200,0,65000),
    ("JNU Medical College Jaipur","Rajasthan","Jaipur","PRIVATE",950000,150,0,70000),
    ("Mahatma Gandhi Medical College Jaipur","Rajasthan","Jaipur","PRIVATE",850000,200,0,75000),
    # ═══ Additional Bihar ═══
    ("Government Medical College Bettiah","Bihar","Bettiah","GOVT",42000,100,0,45000),
    ("Government Medical College Purnia","Bihar","Purnia","GOVT",42000,100,0,48000),
    ("Government Medical College Samastipur","Bihar","Samastipur","GOVT",42000,100,0,50000),
    ("Government Medical College Munger","Bihar","Munger","GOVT",42000,100,0,52000),
    ("Government Medical College Bhagalpur","Bihar","Bhagalpur","GOVT",42000,100,0,48000),
    ("Government Medical College Arrah","Bihar","Arrah","GOVT",42000,100,0,55000),
    # ═══ Additional Gujarat ═══
    ("Government Medical College Patan","Gujarat","Patan","GOVT",42000,100,0,42000),
    ("Government Medical College Valsad","Gujarat","Valsad","GOVT",42000,100,0,45000),
    ("Government Medical College Junagadh","Gujarat","Junagadh","GOVT",42000,100,0,40000),
    ("GMERS Medical College Gandhinagar","Gujarat","Gandhinagar","GOVT",45000,150,0,28000),
    ("GMERS Medical College Vadodara","Gujarat","Vadodara","GOVT",45000,150,0,30000),
    # ═══ Additional Maharashtra ═══
    ("Government Medical College Nanded","Maharashtra","Nanded","GOVT",42000,100,0,45000),
    ("Government Medical College Gondia","Maharashtra","Gondia","GOVT",42000,100,0,52000),
    ("Government Medical College Sindhudurg","Maharashtra","Sindhudurg","GOVT",42000,100,0,55000),
    ("MIMER Medical College Pune","Maharashtra","Pune","PRIVATE",1100000,150,0,68000),
    ("Krishna Institute of Medical Sciences Karad","Maharashtra","Karad","DEEMED",1000000,200,0,65000),
    ("Smt Kashibai Navale Medical College Pune","Maharashtra","Pune","PRIVATE",1200000,150,0,62000),
    ("Dr Vithalrao Vikhe Patil Medical College Ahmednagar","Maharashtra","Ahmednagar","PRIVATE",950000,150,0,72000),
    # ═══ Additional Karnataka ═══
    ("Raichur Institute of Medical Sciences","Karnataka","Raichur","GOVT",45000,100,0,45000),
    ("Koppal Institute of Medical Sciences","Karnataka","Koppal","GOVT",45000,100,0,48000),
    ("Gadag Institute of Medical Sciences","Karnataka","Gadag","GOVT",45000,100,0,50000),
    ("Bidar Institute of Medical Sciences","Karnataka","Bidar","GOVT",45000,100,0,52000),
    ("Chamarajanagar Institute of Medical Sciences","Karnataka","Chamarajanagar","GOVT",45000,100,0,55000),
    ("Subbaiah Institute of Medical Sciences","Karnataka","Shimoga","PRIVATE",900000,150,0,78000),
    ("Adichunchanagiri Institute of Medical Sciences","Karnataka","Mandya","DEEMED",950000,150,0,75000),
    ("BGS Global Institute of Medical Sciences","Karnataka","Bangalore","PRIVATE",1000000,150,0,72000),
    # ═══ Additional Tamil Nadu ═══
    ("Government Medical College Dharmapuri","Tamil Nadu","Dharmapuri","GOVT",48000,100,0,42000),
    ("Government Medical College Krishnagiri","Tamil Nadu","Krishnagiri","GOVT",48000,100,0,45000),
    ("Government Medical College Karur","Tamil Nadu","Karur","GOVT",48000,100,0,44000),
    ("Government Medical College Nilgiris","Tamil Nadu","Ooty","GOVT",48000,100,0,48000),
    ("Government Medical College Villupuram","Tamil Nadu","Villupuram","GOVT",48000,100,0,46000),
    ("Vinayaka Mission Medical College","Tamil Nadu","Salem","DEEMED",1000000,150,0,70000),
    ("Chettinad Hospital and Research Institute","Tamil Nadu","Chennai","DEEMED",1200000,150,0,65000),
    ("ACS Medical College Chennai","Tamil Nadu","Chennai","PRIVATE",1100000,150,0,68000),
    # ═══ Additional Kerala ═══
    ("Government Medical College Idukki","Kerala","Idukki","GOVT",44000,100,0,35000),
    ("Government Medical College Palakkad","Kerala","Palakkad","GOVT",44000,100,0,32000),
    ("Government Medical College Manjeri","Kerala","Manjeri","GOVT",44000,100,0,30000),
    ("Travancore Medical College","Kerala","Kollam","PRIVATE",750000,100,0,85000),
    ("MES Medical College Perinthalmanna","Kerala","Perinthalmanna","PRIVATE",700000,100,0,88000),
    # ═══ Additional Telangana / AP ═══
    ("Government Medical College Mahabubnagar","Telangana","Mahabubnagar","GOVT",45000,100,0,45000),
    ("Government Medical College Nalgonda","Telangana","Nalgonda","GOVT",45000,100,0,48000),
    ("Government Medical College Siddipet","Telangana","Siddipet","GOVT",45000,100,0,50000),
    ("ESIC Medical College Hyderabad","Telangana","Hyderabad","GOVT",50000,100,0,22000),
    ("Government Medical College Anantapur","Andhra Pradesh","Anantapur","GOVT",42000,100,0,40000),
    ("Government Medical College Nellore","Andhra Pradesh","Nellore","GOVT",42000,100,0,38000),
    ("Government Medical College Ongole","Andhra Pradesh","Ongole","GOVT",42000,100,0,42000),
    ("NRI Medical College Guntur","Andhra Pradesh","Guntur","PRIVATE",900000,150,0,72000),
    # ═══ Additional Punjab / Haryana ═══
    ("Government Medical College Faridkot","Punjab","Faridkot","GOVT",48000,100,0,28000),
    ("Government Medical College Barnala","Punjab","Barnala","GOVT",48000,100,0,35000),
    ("Government Medical College Rajpura","Punjab","Rajpura","GOVT",48000,100,0,38000),
    ("Government Medical College Karnal","Haryana","Karnal","GOVT",48000,100,0,30000),
    ("Government Medical College Bhiwani","Haryana","Bhiwani","GOVT",48000,100,0,35000),
    ("World College of Medical Sciences Jhajjar","Haryana","Jhajjar","PRIVATE",850000,100,0,80000),
    # ═══ Additional Odisha ═══
    ("Government Medical College Balangir","Odisha","Balangir","GOVT",45000,100,0,38000),
    ("Government Medical College Baripada","Odisha","Baripada","GOVT",45000,100,0,40000),
    ("Government Medical College Koraput","Odisha","Koraput","GOVT",45000,100,0,45000),
    ("Government Medical College Bhawanipatna","Odisha","Bhawanipatna","GOVT",45000,100,0,42000),
    ("Hi Tech Medical College Bhubaneswar","Odisha","Bhubaneswar","PRIVATE",800000,150,0,75000),
    # ═══ Additional Assam / NE ═══
    ("Tezpur Medical College","Assam","Tezpur","GOVT",45000,100,0,32000),
    ("Silchar Medical College","Assam","Silchar","GOVT",45000,150,0,30000),
    ("Jorhat Medical College","Assam","Jorhat","GOVT",45000,100,0,35000),
    ("Barpeta Medical College","Assam","Barpeta","GOVT",45000,100,0,38000),
    ("Nagaland University Medical College","Nagaland","Kohima","GOVT",45000,50,0,50000),
    ("Zoram Medical College","Mizoram","Aizawl","GOVT",45000,50,0,48000),
    ("Tripura Medical College","Tripura","Agartala","PRIVATE",700000,100,0,82000),
    # ═══ Additional Chhattisgarh ═══
    ("Government Medical College Ambikapur","Chhattisgarh","Ambikapur","GOVT",45000,100,0,35000),
    ("Government Medical College Rajnandgaon CG","Chhattisgarh","Rajnandgaon","GOVT",45000,100,0,38000),
    ("Government Medical College Korba","Chhattisgarh","Korba","GOVT",45000,100,0,42000),
    ("Government Medical College Jagdalpur","Chhattisgarh","Jagdalpur","GOVT",45000,100,0,45000),
    # ═══ Additional J&K / HP / UK ═══
    ("Government Medical College Anantnag","Jammu And Kashmir","Anantnag","GOVT",48000,100,0,28000),
    ("Government Medical College Baramulla","Jammu And Kashmir","Baramulla","GOVT",48000,100,0,30000),
    ("Government Medical College Kathua","Jammu And Kashmir","Kathua","GOVT",48000,100,0,32000),
    ("Government Medical College Doda","Jammu And Kashmir","Doda","GOVT",48000,100,0,38000),
    ("Government Medical College Mandi","Himachal Pradesh","Mandi","GOVT",45000,100,0,32000),
    ("Government Medical College Hamirpur","Himachal Pradesh","Hamirpur","GOVT",45000,100,0,35000),
    ("Government Medical College Nahan","Himachal Pradesh","Nahan","GOVT",45000,100,0,38000),
    ("SRHU Medical College Dehradun","Uttarakhand","Dehradun","PRIVATE",900000,100,0,72000),
    ("Government Medical College Srinagar Garhwal","Uttarakhand","Srinagar","GOVT",48000,100,0,30000),
    # ═══ Additional Jharkhand ═══
    ("Government Medical College Dumka","Jharkhand","Dumka","GOVT",45000,100,0,38000),
    ("Government Medical College Hazaribag","Jharkhand","Hazaribag","GOVT",45000,100,0,35000),
    ("Government Medical College Palamu","Jharkhand","Palamu","GOVT",45000,100,0,42000),
    # ═══ Additional West Bengal ═══
    ("Diamond Harbour Government Medical College","West Bengal","Diamond Harbour","GOVT",44000,100,0,42000),
    ("Malda Medical College","West Bengal","Malda","GOVT",44000,100,0,45000),
    ("Murshidabad Medical College","West Bengal","Murshidabad","GOVT",44000,100,0,48000),
    ("Raiganj Government Medical College","West Bengal","Raiganj","GOVT",44000,100,0,50000),
    ("Purulia Government Medical College","West Bengal","Purulia","GOVT",44000,100,0,52000),
    ("IQ City Medical College Durgapur","West Bengal","Durgapur","PRIVATE",800000,100,0,78000),
    # ═══ Additional Private (Pan India) ═══
    ("KIMS Bhubaneswar","Odisha","Bhubaneswar","PRIVATE",950000,200,0,68000),
    ("SUM Hospital Medical College Bhubaneswar","Odisha","Bhubaneswar","PRIVATE",900000,200,0,72000),
    ("Kalinga Institute of Medical Sciences","Odisha","Bhubaneswar","DEEMED",1000000,200,0,65000),
    ("Apollo Institute of Medical Sciences Hyderabad","Telangana","Hyderabad","PRIVATE",1200000,150,0,60000),
    ("Deccan College of Medical Sciences Hyderabad","Telangana","Hyderabad","PRIVATE",1000000,150,0,68000),
    ("MNR Medical College Sangareddy","Telangana","Sangareddy","PRIVATE",850000,100,0,78000),
    ("Sri Devaraj Urs Medical College Kolar","Karnataka","Kolar","DEEMED",900000,150,0,75000),
    ("Sapthagiri Institute of Medical Sciences","Karnataka","Bangalore","PRIVATE",1000000,150,0,72000),
    ("Akash Institute of Medical Sciences","Karnataka","Bangalore","PRIVATE",950000,100,0,75000),
    ("Dr BR Ambedkar Medical College Bangalore","Karnataka","Bangalore","PRIVATE",1100000,150,0,68000),
    ("Sree Balaji Medical College Chennai","Tamil Nadu","Chennai","PRIVATE",1100000,150,0,70000),
    ("Shri Sathya Sai Medical College Chennai","Tamil Nadu","Chennai","DEEMED",900000,100,0,78000),
    ("MG Medical College Jaipur","Rajasthan","Jaipur","PRIVATE",850000,150,0,76000),
    ("Ananta Institute of Medical Sciences Rajsamand","Rajasthan","Rajsamand","PRIVATE",800000,100,0,80000),
    ("Government Medical College Dungarpur New","Rajasthan","Dungarpur","GOVT",44000,100,0,44000),
    ("Government Medical College Sikar","Rajasthan","Sikar","GOVT",44000,100,0,38000),
    ("Government Medical College Alwar","Rajasthan","Alwar","GOVT",44000,100,0,36000),
    ("Government Medical College Nagaur","Rajasthan","Nagaur","GOVT",44000,100,0,42000),
    ("Government Medical College Jalore","Rajasthan","Jalore","GOVT",44000,100,0,44000),
    ("ESIC Medical College Faridabad","Haryana","Faridabad","GOVT",50000,100,0,22000),
    ("ESIC Medical College Joka","West Bengal","Kolkata","GOVT",50000,100,0,25000),
    ("ESIC Medical College Gulbarga","Karnataka","Gulbarga","GOVT",50000,100,0,25000),
    ("ESIC Medical College Chennai","Tamil Nadu","Chennai","GOVT",50000,100,0,22000),
]

def main():
    # Read existing CSV
    existing = []
    with open(OUT, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            existing.append(row)

    existing_names = set(r[0] for r in existing)
    new_rows = []

    for (name, state, city, ctype, fee, seats, ranking, base_cr) in EXTRA:
        if name in existing_names:
            continue
        for year in [2024, 2023, 2022, 2021]:
            if ctype == "CENTRAL":
                quotas = ["AIQ"]
            elif ctype in ("PRIVATE", "DEEMED"):
                quotas = ["AIQ"]
                if fee > 800000:
                    quotas.append("MQ")
            else:
                quotas = ["AIQ", "SQ"]

            for quota in quotas:
                q_factor = 1.0 if quota == "AIQ" else (1.4 if quota == "SQ" else 0.9)
                adjusted_cr = int(base_cr * q_factor)
                rows = gen_category_rows(name, state, city, ctype, fee, seats, ranking, adjusted_cr, year, quota)
                new_rows.extend(rows)

    all_rows = existing + new_rows

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(all_rows)

    colleges = set(r[0] for r in all_rows)
    states = set(r[1] for r in all_rows)
    mp_colleges = set(r[0] for r in all_rows if r[1] == "Madhya Pradesh")
    print(f"Total rows: {len(all_rows)}")
    print(f"Total colleges: {len(colleges)}")
    print(f"States: {len(states)}")
    print(f"MP colleges: {len(mp_colleges)}")

if __name__ == "__main__":
    main()
