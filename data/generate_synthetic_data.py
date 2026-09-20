#!/usr/bin/env python3
"""
Synthetic Criminal Network Dataset Generator
Generates realistic interconnected criminal data for the Network Analysis System demo.
"""

import csv
import random
import os
import json
from datetime import datetime, timedelta

random.seed(42)

# ── Configuration ──────────────────────────────────────────────
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
NUM_SUSPECTS = 80
NUM_INCIDENTS = 500
NUM_CDR_RECORDS = 5000
NUM_FINANCIAL_TXN = 2000
NUM_CRIMINAL_HISTORY = 300

# ── Name / Entity Pools ───────────────────────────────────────
FIRST_NAMES = [
    "Rajesh", "Amit", "Suresh", "Vikram", "Arjun", "Deepak", "Rahul", "Manoj",
    "Sanjay", "Ajay", "Ravi", "Prakash", "Naveen", "Kiran", "Ashok", "Vinod",
    "Ramesh", "Sunil", "Anil", "Mohan", "Priya", "Neha", "Anita", "Sunita",
    "Kavita", "Pooja", "Rekha", "Meena", "Geeta", "Suman", "Farooq", "Imran",
    "Saleem", "Tariq", "Hassan", "Yusuf", "Abdul", "Rizwan", "Carlos", "Miguel"
]

LAST_NAMES = [
    "Sharma", "Verma", "Singh", "Kumar", "Gupta", "Patel", "Yadav", "Chauhan",
    "Reddy", "Joshi", "Mishra", "Pandey", "Thakur", "Agarwal", "Saxena", "Mehta",
    "Shah", "Das", "Roy", "Khan", "Ahmed", "Ali", "Hussain", "Malik", "Qureshi",
    "Garcia", "Rodriguez", "Martinez", "Lopez", "Hernandez"
]

ORGANIZATIONS = [
    "Shadow Syndicate", "Red Lotus Gang", "Northern Alliance Network",
    "Metro Finance Corp", "Apex Trading LLC", "Golden Circle Imports",
    "Bluestone Holdings", "Iron Gate Security", "Falcon Express Logistics",
    "Emerald Bay Enterprises", "Crescent Moon Foundation", "Diamond Rock Mining",
    "Silver Line Transport", "Vortex Communications", "Nighthawk Operations",
    "Zenith Capital Group", "Dark Web Solutions", "Phantom Industries"
]

LOCATIONS = [
    "Sector 15, New Delhi", "Marine Drive, Mumbai", "MG Road, Bangalore",
    "Park Street, Kolkata", "Jubilee Hills, Hyderabad", "Anna Nagar, Chennai",
    "Aundh, Pune", "Navrangpura, Ahmedabad", "Civil Lines, Lucknow",
    "Koregaon Park, Pune", "Banjara Hills, Hyderabad", "Indiranagar, Bangalore",
    "Salt Lake, Kolkata", "Connaught Place, New Delhi", "Andheri West, Mumbai",
    "Velachery, Chennai", "Gomti Nagar, Lucknow", "Satellite, Ahmedabad",
    "Kothrud, Pune", "Malviya Nagar, Jaipur", "45th Street Warehouse",
    "Industrial Zone B-12", "Old Market Area", "Railway Station Complex",
    "Highway NH-48 Rest Stop", "Port District Dock 7", "Airport Cargo Terminal",
    "Bus Terminal Underground", "Abandoned Factory Block C", "River Bridge Underpass"
]

VEHICLE_TYPES = ["Car", "Motorcycle", "SUV", "Van", "Truck", "Auto-rickshaw"]
VEHICLE_MAKES = ["Maruti", "Hyundai", "Honda", "Toyota", "Mahindra", "Tata", "BMW", "Mercedes"]

CRIME_TYPES = [
    "ASSAULT", "BATTERY", "BURGLARY", "CRIMINAL DAMAGE", "ROBBERY",
    "NARCOTICS", "WEAPONS VIOLATION", "MOTOR VEHICLE THEFT",
    "DECEPTIVE PRACTICE", "THEFT", "CRIMINAL TRESPASS",
    "OFFENSE INVOLVING CHILDREN", "OTHER OFFENSE", "KIDNAPPING",
    "EXTORTION", "MONEY LAUNDERING", "CYBER CRIME", "HUMAN TRAFFICKING"
]

LOCATION_DESCRIPTIONS = [
    "STREET", "RESIDENCE", "APARTMENT", "SIDEWALK", "ALLEY",
    "PARKING LOT", "RESTAURANT", "COMMERCIAL BUILDING", "HOTEL",
    "GAS STATION", "BANK", "SCHOOL", "PARK", "WAREHOUSE", "VEHICLE"
]


# ── Helper Functions ──────────────────────────────────────────
def generate_phone():
    return f"+91-{random.randint(70000, 99999)}{random.randint(10000, 99999)}"

def generate_vehicle_plate():
    state = random.choice(["DL", "MH", "KA", "TN", "UP", "HR", "RJ", "GJ"])
    return f"{state}-{random.randint(1,99):02d}-{random.choice('ABCDEFGHJKLMNPRSTUVWXY')}{random.choice('ABCDEFGHJKLMNPRSTUVWXY')}-{random.randint(1000,9999)}"

def random_date(start_year=2023, end_year=2024):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    rand_days = random.randint(0, delta.days)
    rand_secs = random.randint(0, 86399)
    return start + timedelta(days=rand_days, seconds=rand_secs)

def generate_case_id():
    return f"FIR-{random.randint(2023, 2024)}-{random.randint(10000, 99999)}"


# ── Generate Suspects (People) ────────────────────────────────
def generate_suspects():
    suspects = []
    for i in range(NUM_SUSPECTS):
        fname = random.choice(FIRST_NAMES)
        lname = random.choice(LAST_NAMES)
        suspect = {
            "id": f"S{i+1:04d}",
            "name": f"{fname} {lname}",
            "age": random.randint(19, 62),
            "gender": random.choice(["Male", "Female"]),
            "phone": generate_phone(),
            "phone2": generate_phone() if random.random() < 0.3 else "",
            "known_associates": [],
            "organization": random.choice(ORGANIZATIONS) if random.random() < 0.45 else "",
            "address": random.choice(LOCATIONS),
            "vehicles": [],
            "risk_level": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
        }
        if random.random() < 0.4:
            suspect["vehicles"].append({
                "plate": generate_vehicle_plate(),
                "type": random.choice(VEHICLE_TYPES),
                "make": random.choice(VEHICLE_MAKES)
            })
        suspects.append(suspect)

    # Create criminal network clusters (5 clusters of varying sizes)
    cluster_sizes = [12, 10, 8, 15, 7, 6, 5, 4, 3, 10]
    idx = 0
    for cluster_size in cluster_sizes:
        cluster_members = suspects[idx:idx + cluster_size]
        # Connect members within cluster
        for s in cluster_members:
            n_assoc = random.randint(1, min(4, len(cluster_members) - 1))
            assoc_pool = [m["id"] for m in cluster_members if m["id"] != s["id"]]
            s["known_associates"] = random.sample(assoc_pool, min(n_assoc, len(assoc_pool)))
        idx += cluster_size

    # Add some cross-cluster connections (intermediaries)
    for _ in range(15):
        s1 = random.choice(suspects)
        s2 = random.choice(suspects)
        if s1["id"] != s2["id"] and s2["id"] not in s1["known_associates"]:
            s1["known_associates"].append(s2["id"])

    return suspects


# ── Generate FIR / Incident Reports ──────────────────────────
NARRATIVE_TEMPLATES = [
    "On {date}, suspect {suspect1} was observed meeting {suspect2} at {location}. "
    "The meeting lasted approximately {duration} minutes. Suspect was seen carrying a {item}. "
    "Vehicle with plate {plate} was parked nearby. Contact phone {phone} was intercepted.",

    "Investigation report: {suspect1} allegedly transferred funds to {suspect2} via {org} on {date}. "
    "Transaction of ₹{amount} was flagged. Both suspects are known to frequent {location}. "
    "Surveillance indicates regular communication through phone {phone}.",

    "FIR filed against {suspect1} for {crime_type} at {location} on {date}. "
    "Witnesses identified accomplice {suspect2} at the scene. "
    "A {vehicle_type} ({plate}) was used to flee. {suspect1} is associated with {org}.",

    "Intelligence report: {suspect1} and {suspect2} are part of a network operating from {location}. "
    "Phone intercept of {phone} revealed plans for {crime_type} targeting {target_location}. "
    "Organization {org} is suspected to be a front for illegal activities.",

    "Arrest report: {suspect1} apprehended on {date} at {location} in connection with {crime_type}. "
    "During interrogation, {suspect1} revealed association with {suspect2} and {org}. "
    "Recovered items include {item}. Phone {phone} seized for analysis.",

    "Confidential informant reports that {suspect1} has been coordinating with {suspect2} "
    "through encrypted communications. Activities centered around {location} and {target_location}. "
    "Financial trail leads to {org}. Estimated proceeds: ₹{amount}.",

    "Surveillance report #{case_id}: Subject {suspect1} traveled to {location} on {date}. "
    "Met with {suspect2} and an unidentified individual. Discussion about {crime_type} "
    "operations was overheard. Subject departed in {vehicle_type} bearing plate {plate}.",

    "Crime scene report: {crime_type} occurred at {location} on {date}. "
    "Evidence points to involvement of {suspect1}. CCTV footage shows {suspect2} "
    "in the vicinity. {org} financial records show payment of ₹{amount} on same date. "
    "Phone {phone} location data places suspect at scene."
]

ITEMS = [
    "suspicious package", "briefcase", "laptop bag", "duffel bag",
    "sealed envelope", "mobile phones (3)", "counterfeit currency",
    "unregistered firearm", "chemical substances", "forged documents",
    "encrypted hard drive", "cash bundle"
]


def generate_incidents(suspects):
    incidents = []
    for i in range(NUM_INCIDENTS):
        s1 = random.choice(suspects)
        # Prefer associates for s2 to build realistic networks
        if s1["known_associates"] and random.random() < 0.7:
            s2_id = random.choice(s1["known_associates"])
            s2 = next((s for s in suspects if s["id"] == s2_id), random.choice(suspects))
        else:
            s2 = random.choice(suspects)

        dt = random_date()
        crime = random.choice(CRIME_TYPES)
        loc = random.choice(LOCATIONS)
        org = s1.get("organization") or random.choice(ORGANIZATIONS)
        plate = s1["vehicles"][0]["plate"] if s1["vehicles"] else generate_vehicle_plate()
        vtype = s1["vehicles"][0]["type"] if s1["vehicles"] else random.choice(VEHICLE_TYPES)

        narrative = random.choice(NARRATIVE_TEMPLATES).format(
            date=dt.strftime("%Y-%m-%d %H:%M"),
            suspect1=s1["name"],
            suspect2=s2["name"],
            location=loc,
            target_location=random.choice(LOCATIONS),
            duration=random.randint(10, 120),
            item=random.choice(ITEMS),
            plate=plate,
            phone=s1["phone"],
            amount=random.randint(10000, 5000000),
            org=org,
            crime_type=crime,
            vehicle_type=vtype,
            case_id=generate_case_id()
        )

        incident = {
            "incident_id": f"INC-{i+1:05d}",
            "case_id": generate_case_id(),
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%H:%M:%S"),
            "crime_type": crime,
            "location": loc,
            "location_description": random.choice(LOCATION_DESCRIPTIONS),
            "beat": random.randint(100, 2500),
            "district": random.randint(1, 25),
            "community_area": random.randint(1, 77),
            "suspect1_id": s1["id"],
            "suspect1_name": s1["name"],
            "suspect2_id": s2["id"],
            "suspect2_name": s2["name"],
            "narrative": narrative,
            "arrest": random.choice([True, False]),
            "domestic": random.random() < 0.15,
            "latitude": round(random.uniform(28.4, 28.8), 6),
            "longitude": round(random.uniform(76.8, 77.4), 6),
        }
        incidents.append(incident)
    return incidents


# ── Generate CDR Records ─────────────────────────────────────
def generate_cdr(suspects):
    records = []
    phones = {s["id"]: s["phone"] for s in suspects}
    phone2s = {s["id"]: s["phone2"] for s in suspects if s["phone2"]}

    for i in range(NUM_CDR_RECORDS):
        s1 = random.choice(suspects)
        # 70% chance to call a known associate
        if s1["known_associates"] and random.random() < 0.7:
            s2_id = random.choice(s1["known_associates"])
        else:
            s2_id = random.choice(suspects)["id"]

        caller_phone = phones.get(s1["id"], generate_phone())
        # Sometimes use secondary phone
        if s1["id"] in phone2s and random.random() < 0.2:
            caller_phone = phone2s[s1["id"]]

        receiver_phone = phones.get(s2_id, generate_phone())

        dt = random_date()
        duration = random.randint(5, 3600)  # 5 sec to 1 hour
        call_type = random.choices(["VOICE", "SMS", "DATA"], weights=[50, 35, 15])[0]

        record = {
            "cdr_id": f"CDR-{i+1:06d}",
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%H:%M:%S"),
            "caller_id": s1["id"],
            "caller_phone": caller_phone,
            "receiver_id": s2_id,
            "receiver_phone": receiver_phone,
            "duration_seconds": duration if call_type == "VOICE" else 0,
            "call_type": call_type,
            "cell_tower_id": f"TWR-{random.randint(1,200):04d}",
            "cell_tower_location": random.choice(LOCATIONS),
            "imei": f"{random.randint(100000000000000, 999999999999999)}",
        }
        records.append(record)
    return records


# ── Generate Financial Transactions ───────────────────────────
TRANSACTION_TYPES = ["WIRE_TRANSFER", "CASH_DEPOSIT", "CASH_WITHDRAWAL",
                     "CHECK", "ONLINE_TRANSFER", "CRYPTO", "HAWALA"]
BANK_NAMES = ["State Bank", "HDFC Bank", "ICICI Bank", "Axis Bank",
              "Punjab National Bank", "Bank of Baroda", "Kotak Bank",
              "Yes Bank", "Federal Bank", "IndusInd Bank"]

def generate_financial(suspects):
    records = []
    for i in range(NUM_FINANCIAL_TXN):
        s1 = random.choice(suspects)
        if s1["known_associates"] and random.random() < 0.6:
            s2_id = random.choice(s1["known_associates"])
            s2 = next((s for s in suspects if s["id"] == s2_id), random.choice(suspects))
        else:
            s2 = random.choice(suspects)

        dt = random_date()
        amount = random.choice([
            random.randint(500, 10000),       # small
            random.randint(10000, 100000),     # medium
            random.randint(100000, 1000000),   # large
            random.randint(1000000, 10000000), # very large (suspicious)
        ])

        record = {
            "txn_id": f"TXN-{i+1:06d}",
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%H:%M:%S"),
            "sender_id": s1["id"],
            "sender_name": s1["name"],
            "sender_account": f"ACCT-{random.randint(100000, 999999)}",
            "receiver_id": s2["id"],
            "receiver_name": s2["name"],
            "receiver_account": f"ACCT-{random.randint(100000, 999999)}",
            "amount": amount,
            "currency": "INR",
            "transaction_type": random.choice(TRANSACTION_TYPES),
            "bank": random.choice(BANK_NAMES),
            "is_suspicious": amount > 500000 or random.random() < 0.1,
            "remarks": random.choice([
                "Regular transfer", "Business payment", "Personal",
                "Investment return", "Loan repayment", "Consulting fee",
                "Property deal", "Import payment", "Commission",
                "No remarks", "Urgent transfer", "Monthly installment"
            ])
        }
        records.append(record)
    return records


# ── Generate Criminal History ─────────────────────────────────
def generate_criminal_history(suspects):
    records = []
    # Only some suspects have criminal history
    suspects_with_history = random.sample(suspects, min(NUM_CRIMINAL_HISTORY, len(suspects)))

    idx = 0
    for s in suspects_with_history:
        n_records = random.randint(1, 5)
        for _ in range(n_records):
            dt = random_date(2018, 2024)
            record = {
                "record_id": f"CR-{idx+1:05d}",
                "suspect_id": s["id"],
                "suspect_name": s["name"],
                "date": dt.strftime("%Y-%m-%d"),
                "crime_type": random.choice(CRIME_TYPES),
                "case_id": generate_case_id(),
                "court": random.choice([
                    "District Court", "Sessions Court", "High Court",
                    "Metropolitan Magistrate", "Special Court"
                ]),
                "status": random.choice([
                    "CONVICTED", "ACQUITTED", "PENDING", "UNDER_TRIAL",
                    "ABSCONDING", "ON_BAIL", "CASE_CLOSED"
                ]),
                "sentence": random.choice([
                    "None", "6 months", "1 year", "2 years", "3 years",
                    "5 years", "7 years", "10 years", "Fine ₹50,000",
                    "Fine ₹1,00,000", "Community service"
                ]),
                "location": random.choice(LOCATIONS),
                "co_accused": random.sample(
                    [x["name"] for x in suspects if x["id"] != s["id"]],
                    k=random.randint(0, 3)
                )
            }
            records.append(record)
            idx += 1
    return records


# ── Write to CSV ──────────────────────────────────────────────
def write_csv(filename, records, fieldnames=None):
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not records:
        return
    if fieldnames is None:
        fieldnames = list(records[0].keys())
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            # Convert lists/dicts to JSON strings for CSV
            row = {}
            for k, v in r.items():
                if isinstance(v, (list, dict)):
                    row[k] = json.dumps(v)
                else:
                    row[k] = v
            writer.writerow(row)
    print(f"  ✓ Written {len(records)} records to {filepath}")


def write_json(filename, data):
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Written {len(data)} records to {filepath}")


# ── Main ──────────────────────────────────────────────────────
def main():
    print("🔧 Generating Synthetic Criminal Network Dataset...")
    print(f"   Output directory: {OUTPUT_DIR}")
    print()

    print("1. Generating suspects...")
    suspects = generate_suspects()
    write_json("suspects.json", suspects)
    write_csv("suspects.csv", [
        {k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in s.items()}
        for s in suspects
    ])

    print("2. Generating incident/FIR reports...")
    incidents = generate_incidents(suspects)
    write_csv("incidents.csv", incidents)

    print("3. Generating CDR records...")
    cdr = generate_cdr(suspects)
    write_csv("cdr_records.csv", cdr)

    print("4. Generating financial transactions...")
    financial = generate_financial(suspects)
    write_csv("financial_transactions.csv", financial)

    print("5. Generating criminal history...")
    history = generate_criminal_history(suspects)
    write_csv("criminal_history.csv", history)

    print()
    print("✅ Dataset generation complete!")
    print(f"   Suspects: {len(suspects)}")
    print(f"   Incidents: {len(incidents)}")
    print(f"   CDR Records: {len(cdr)}")
    print(f"   Financial Transactions: {len(financial)}")
    print(f"   Criminal History Records: {len(history)}")


if __name__ == "__main__":
    main()
