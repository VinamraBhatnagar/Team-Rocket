"""
Data Processor Module
Loads, cleans, and normalizes data from all sources.
Performs entity resolution to link entities across datasets.
"""

import os
import csv
import json
import pandas as pd
from collections import defaultdict


class DataProcessor:
    """Central data ingestion and processing pipeline."""

    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.suspects = []
        self.incidents = []
        self.cdr_records = []
        self.financial_records = []
        self.criminal_history = []
        self.entity_index = {}  # Unified entity lookup
        self._loaded = False

    def load_all(self):
        """Load all data sources."""
        print("📂 Loading data sources...")
        self._load_suspects()
        self._load_incidents()
        self._load_cdr()
        self._load_financial()
        self._load_criminal_history()
        self._build_entity_index()
        self._loaded = True
        print(f"   ✅ Loaded {len(self.suspects)} suspects, {len(self.incidents)} incidents, "
              f"{len(self.cdr_records)} CDR, {len(self.financial_records)} transactions, "
              f"{len(self.criminal_history)} history records")

    def _load_suspects(self):
        path = os.path.join(self.data_dir, "suspects.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                self.suspects = json.load(f)
        else:
            # Fallback to CSV
            path = os.path.join(self.data_dir, "suspects.csv")
            if os.path.exists(path):
                df = pd.read_csv(path)
                self.suspects = df.to_dict('records')
                for s in self.suspects:
                    for field in ['known_associates', 'vehicles']:
                        if field in s and isinstance(s[field], str):
                            try:
                                s[field] = json.loads(s[field])
                            except (json.JSONDecodeError, TypeError):
                                s[field] = []

    def _load_incidents(self):
        path = os.path.join(self.data_dir, "incidents.csv")
        if os.path.exists(path):
            df = pd.read_csv(path)
            self.incidents = df.to_dict('records')

    def _load_cdr(self):
        path = os.path.join(self.data_dir, "cdr_records.csv")
        if os.path.exists(path):
            df = pd.read_csv(path)
            self.cdr_records = df.to_dict('records')

    def _load_financial(self):
        path = os.path.join(self.data_dir, "financial_transactions.csv")
        if os.path.exists(path):
            df = pd.read_csv(path)
            self.financial_records = df.to_dict('records')

    def _load_criminal_history(self):
        path = os.path.join(self.data_dir, "criminal_history.csv")
        if os.path.exists(path):
            df = pd.read_csv(path)
            self.criminal_history = df.to_dict('records')
            for rec in self.criminal_history:
                if 'co_accused' in rec and isinstance(rec['co_accused'], str):
                    try:
                        rec['co_accused'] = json.loads(rec['co_accused'])
                    except (json.JSONDecodeError, TypeError):
                        rec['co_accused'] = []

    def _build_entity_index(self):
        """Build a unified entity index for fast lookups."""
        self.entity_index = {
            "persons": {},
            "phones": {},
            "organizations": {},
            "locations": {},
            "vehicles": {}
        }

        # Index suspects
        for s in self.suspects:
            sid = s.get("id", "")
            name = s.get("name", "")

            self.entity_index["persons"][sid] = {
                "id": sid,
                "name": name,
                "type": "PERSON",
                "phone": s.get("phone", ""),
                "phone2": s.get("phone2", ""),
                "organization": s.get("organization", ""),
                "address": s.get("address", ""),
                "risk_level": s.get("risk_level", "LOW"),
                "age": s.get("age", 0),
                "gender": s.get("gender", ""),
                "incidents": [],
                "calls_made": 0,
                "calls_received": 0,
                "total_sent": 0,
                "total_received": 0,
                "criminal_records": 0,
                "known_associates": s.get("known_associates", []),
                "vehicles": s.get("vehicles", [])
            }

            # Index phones
            if s.get("phone"):
                self.entity_index["phones"][s["phone"]] = sid
            if s.get("phone2"):
                self.entity_index["phones"][s["phone2"]] = sid

            # Index organizations
            if s.get("organization"):
                org = s["organization"]
                if org not in self.entity_index["organizations"]:
                    self.entity_index["organizations"][org] = {
                        "name": org, "type": "ORGANIZATION", "members": []
                    }
                self.entity_index["organizations"][org]["members"].append(sid)

            # Index locations
            if s.get("address"):
                loc = s["address"]
                if loc not in self.entity_index["locations"]:
                    self.entity_index["locations"][loc] = {
                        "name": loc, "type": "LOCATION", "associated_persons": []
                    }
                self.entity_index["locations"][loc]["associated_persons"].append(sid)

        # Enrich from incidents
        for inc in self.incidents:
            for key in ["suspect1_id", "suspect2_id"]:
                sid = str(inc.get(key, ""))
                if sid in self.entity_index["persons"]:
                    self.entity_index["persons"][sid]["incidents"].append(inc.get("incident_id", ""))

        # Enrich from CDR
        for cdr in self.cdr_records:
            cid = str(cdr.get("caller_id", ""))
            rid = str(cdr.get("receiver_id", ""))
            if cid in self.entity_index["persons"]:
                self.entity_index["persons"][cid]["calls_made"] += 1
            if rid in self.entity_index["persons"]:
                self.entity_index["persons"][rid]["calls_received"] += 1

        # Enrich from financial
        for txn in self.financial_records:
            sid = str(txn.get("sender_id", ""))
            rid = str(txn.get("receiver_id", ""))
            amt = float(txn.get("amount", 0))
            if sid in self.entity_index["persons"]:
                self.entity_index["persons"][sid]["total_sent"] += amt
            if rid in self.entity_index["persons"]:
                self.entity_index["persons"][rid]["total_received"] += amt

        # Enrich from criminal history
        for rec in self.criminal_history:
            sid = str(rec.get("suspect_id", ""))
            if sid in self.entity_index["persons"]:
                self.entity_index["persons"][sid]["criminal_records"] += 1

    def get_person(self, person_id):
        """Get detailed person entity."""
        return self.entity_index["persons"].get(person_id)

    def get_all_persons(self):
        """Get all person entities."""
        return list(self.entity_index["persons"].values())

    def get_all_entities(self):
        """Get all entities with counts."""
        return {
            "persons": len(self.entity_index["persons"]),
            "phones": len(self.entity_index["phones"]),
            "organizations": len(self.entity_index["organizations"]),
            "locations": len(self.entity_index["locations"]),
        }

    def get_organizations(self):
        """Get all organizations."""
        return list(self.entity_index["organizations"].values())

    def get_dashboard_stats(self):
        """Get overview statistics for the dashboard."""
        crime_counts = defaultdict(int)
        monthly_counts = defaultdict(int)
        location_counts = defaultdict(int)
        arrest_count = 0
        domestic_count = 0

        for inc in self.incidents:
            crime_counts[inc.get("crime_type", "UNKNOWN")] += 1
            monthly_counts[inc.get("date", "")[:7]] += 1
            location_counts[inc.get("location", "UNKNOWN")] += 1
            if inc.get("arrest") in [True, "True", "true", 1, "1"]:
                arrest_count += 1
            if inc.get("domestic") in [True, "True", "true", 1, "1"]:
                domestic_count += 1

        suspicious_txns = [t for t in self.financial_records
                           if t.get("is_suspicious") in [True, "True", "true", 1, "1"]]

        total_amount = sum(float(t.get("amount", 0)) for t in self.financial_records)
        suspicious_amount = sum(float(t.get("amount", 0)) for t in suspicious_txns)

        # Risk distribution
        risk_counts = defaultdict(int)
        for s in self.suspects:
            risk_counts[s.get("risk_level", "LOW")] += 1

        return {
            "total_incidents": len(self.incidents),
            "total_suspects": len(self.suspects),
            "total_cdr_records": len(self.cdr_records),
            "total_transactions": len(self.financial_records),
            "total_criminal_records": len(self.criminal_history),
            "arrest_count": arrest_count,
            "arrest_rate": round(arrest_count / max(len(self.incidents), 1) * 100, 1),
            "domestic_count": domestic_count,
            "crime_type_distribution": dict(sorted(crime_counts.items(),
                                                    key=lambda x: x[1], reverse=True)),
            "monthly_trend": dict(sorted(monthly_counts.items())),
            "top_locations": dict(sorted(location_counts.items(),
                                          key=lambda x: x[1], reverse=True)[:10]),
            "suspicious_transactions": len(suspicious_txns),
            "total_transaction_amount": total_amount,
            "suspicious_transaction_amount": suspicious_amount,
            "risk_distribution": dict(risk_counts),
            "organizations_count": len(self.entity_index["organizations"]),
        }

    def get_incidents_for_person(self, person_id):
        """Get all incidents involving a specific person."""
        return [inc for inc in self.incidents
                if str(inc.get("suspect1_id")) == person_id
                or str(inc.get("suspect2_id")) == person_id]

    def get_cdr_for_person(self, person_id):
        """Get all CDR records for a person."""
        return [cdr for cdr in self.cdr_records
                if str(cdr.get("caller_id")) == person_id
                or str(cdr.get("receiver_id")) == person_id]

    def get_transactions_for_person(self, person_id):
        """Get all financial transactions for a person."""
        return [txn for txn in self.financial_records
                if str(txn.get("sender_id")) == person_id
                or str(txn.get("receiver_id")) == person_id]

    def get_history_for_person(self, person_id):
        """Get criminal history for a person."""
        return [rec for rec in self.criminal_history
                if str(rec.get("suspect_id")) == person_id]

    def search_entities(self, query):
        """Search across all entity types."""
        query = query.lower()
        results = []
        for pid, person in self.entity_index["persons"].items():
            if query in person["name"].lower() or query in pid.lower():
                results.append({"type": "PERSON", "id": pid, "name": person["name"],
                                "risk_level": person["risk_level"]})
        for org_name, org in self.entity_index["organizations"].items():
            if query in org_name.lower():
                results.append({"type": "ORGANIZATION", "id": org_name, "name": org_name,
                                "members": len(org["members"])})
        for loc_name, loc in self.entity_index["locations"].items():
            if query in loc_name.lower():
                results.append({"type": "LOCATION", "id": loc_name, "name": loc_name,
                                "associated_persons": len(loc["associated_persons"])})
        return results[:50]

    def get_timeline(self, person_id=None):
        """Get chronological timeline of events, optionally filtered by person."""
        events = []
        for inc in self.incidents:
            if person_id and str(inc.get("suspect1_id")) != person_id and str(inc.get("suspect2_id")) != person_id:
                continue
            events.append({
                "date": inc.get("date", ""),
                "time": inc.get("time", ""),
                "type": "INCIDENT",
                "title": f"{inc.get('crime_type', 'Unknown')} - {inc.get('incident_id', '')}",
                "description": inc.get("narrative", "")[:200],
                "location": inc.get("location", ""),
                "entities": [inc.get("suspect1_name", ""), inc.get("suspect2_name", "")]
            })

        events.sort(key=lambda x: f"{x['date']} {x['time']}")
        return events[:200]
