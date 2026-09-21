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

    def search_suspects(self, query=""):
        """Search suspects with rich details for dossier selection."""
        query = (query or "").lower().strip()
        results = []
        for pid, p in self.entity_index["persons"].items():
            name = p.get("name", "")
            phone = p.get("phone", "")
            org = p.get("organization", "")
            address = p.get("address", "")
            if not query or query in name.lower() or query in pid.lower() or query in phone.lower() or query in org.lower() or query in address.lower():
                results.append({
                    "id": pid,
                    "name": name,
                    "risk_level": p.get("risk_level", "LOW"),
                    "organization": org,
                    "phone": phone,
                    "incidents_count": len(p.get("incidents", [])),
                    "calls_count": (p.get("calls_made", 0) + p.get("calls_received", 0)),
                    "records_count": p.get("criminal_records", 0),
                    "address": address,
                    "age": p.get("age", ""),
                    "gender": p.get("gender", ""),
                })
        risk_weights = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        results.sort(key=lambda x: (risk_weights.get(x["risk_level"], 0), x["incidents_count"]), reverse=True)
        return results[:50]

    def get_person_life_record(self, person_id):
        """
        Compile a complete chronological life record and activity log for a person,
        including judicial court cases, crime incidents, phone intercepts, and financial events.
        """
        events = []
        pid_str = str(person_id)

        # 1. Judicial Records & Prior History
        history = self.get_history_for_person(pid_str)
        for h in history:
            events.append({
                "date": str(h.get("date", "2020-01-01")),
                "time": "09:00:00",
                "type": "JUDICIAL_RECORD",
                "badge": "COURT",
                "title": f"Charge: {h.get('crime_type', 'Offense')} ({h.get('case_id', '')})",
                "description": f"Jurisdiction: {h.get('court', 'Court')}. Disposition: {h.get('status', 'PENDING')}. Sentence: {h.get('sentence', 'N/A')}.",
                "location": h.get("location", ""),
                "severity": "CRITICAL" if h.get("status") == "CONVICTED" else "HIGH",
                "entities": [h.get("suspect_name", "")]
            })

        # 2. Crime Incidents (FIRs)
        incidents = self.get_incidents_for_person(pid_str)
        for inc in incidents:
            co_accused = []
            if inc.get("suspect1_name") and str(inc.get("suspect1_id")) != pid_str:
                co_accused.append(inc.get("suspect1_name"))
            if inc.get("suspect2_name") and str(inc.get("suspect2_id")) != pid_str:
                co_accused.append(inc.get("suspect2_name"))

            arrest_note = "Arrested at scene." if inc.get("arrest") in [True, "True", "true", 1, "1"] else "Suspect fled / warrant active."
            events.append({
                "date": str(inc.get("date", "")),
                "time": str(inc.get("time", "12:00:00")),
                "type": "CRIME_INCIDENT",
                "badge": "FIR",
                "title": f"{inc.get('crime_type', 'Incident')} ({inc.get('incident_id', '')})",
                "description": f"{inc.get('narrative', '')[:220]} [{arrest_note}]",
                "location": inc.get("location", ""),
                "severity": "CRITICAL" if inc.get("crime_type") in ["HOMICIDE", "ARMED ROBBERY", "NARCOTICS TRAFFICKING", "WEAPONS VIOLATION"] else "HIGH",
                "entities": co_accused
            })

        # 3. Major / Suspicious Financial Transactions
        transactions = self.get_transactions_for_person(pid_str)
        for tx in transactions:
            is_sender = str(tx.get("sender_id")) == pid_str
            flow = "Sent" if is_sender else "Received"
            counterparty = tx.get("receiver_name") if is_sender else tx.get("sender_name")
            is_susp = tx.get("is_suspicious") in [True, "True", "true", 1, "1"]

            events.append({
                "date": str(tx.get("date", "")),
                "time": str(tx.get("time", "14:00:00")),
                "type": "FINANCIAL_TRANSACTION",
                "badge": "HAWALA" if tx.get("transaction_type") == "HAWALA" else "TXN",
                "title": f"₹{float(tx.get('amount', 0)):,.0f} {tx.get('transaction_type', 'Transfer')} ({flow})",
                "description": f"{flow} ₹{float(tx.get('amount', 0)):,.0f} {'to' if is_sender else 'from'} {counterparty} via {tx.get('bank')}. Remarks: {tx.get('remarks') or 'None'}",
                "location": tx.get("bank", ""),
                "severity": "CRITICAL" if is_susp else "MEDIUM",
                "entities": [counterparty] if counterparty else []
            })

        # 4. Telecommunication Intercepts (Top 30 representative calls)
        cdr = self.get_cdr_for_person(pid_str)
        for c in cdr[:30]:
            is_caller = str(c.get("caller_id")) == pid_str
            dir_str = "Outbound call to" if is_caller else "Inbound call from"
            other_phone = c.get("receiver_phone") if is_caller else c.get("caller_phone")
            events.append({
                "date": str(c.get("date", "")),
                "time": str(c.get("time", "18:00:00")),
                "type": "TELECOM_INTERCEPT",
                "badge": "CDR",
                "title": f"{c.get('call_type', 'VOICE')} Intercept ({c.get('duration_seconds', 0)}s)",
                "description": f"{dir_str} {other_phone} registered at Cell Tower '{c.get('cell_tower_location', 'Unknown')}'.",
                "location": c.get("cell_tower_location", ""),
                "severity": "LOW",
                "entities": [other_phone] if other_phone else []
            })

        events.sort(key=lambda x: f"{x['date']} {x['time']}", reverse=True)
        return events

    def get_person_dossier_data(self, person_id):
        """
        Aggregate complete intelligence data for rendering and exporting a suspect dossier.
        """
        person = self.get_person(person_id)
        if not person:
            return None

        incidents = self.get_incidents_for_person(person_id)
        cdr = self.get_cdr_for_person(person_id)
        transactions = self.get_transactions_for_person(person_id)
        history = self.get_history_for_person(person_id)
        timeline = self.get_person_life_record(person_id)

        # Resolve associates
        resolved_associates = []
        for aid in person.get("known_associates", []):
            assoc_person = self.get_person(aid)
            if assoc_person:
                resolved_associates.append({
                    "id": assoc_person.get("id"),
                    "name": assoc_person.get("name"),
                    "risk_level": assoc_person.get("risk_level", "LOW"),
                    "organization": assoc_person.get("organization", ""),
                    "phone": assoc_person.get("phone", "")
                })
            else:
                resolved_associates.append({
                    "id": aid,
                    "name": aid,
                    "risk_level": "UNKNOWN",
                    "organization": "",
                    "phone": ""
                })

        # Statistics
        total_sent = sum(float(t.get("amount", 0)) for t in transactions if str(t.get("sender_id")) == person_id)
        total_received = sum(float(t.get("amount", 0)) for t in transactions if str(t.get("receiver_id")) == person_id)
        suspicious_txns = sum(1 for t in transactions if t.get("is_suspicious") in [True, "True", "true", 1, "1"])
        calls_made = sum(1 for c in cdr if str(c.get("caller_id")) == person_id)
        calls_received = sum(1 for c in cdr if str(c.get("receiver_id")) == person_id)

        return {
            "entity": person,
            "incidents": incidents,
            "cdr_records": cdr,
            "transactions": transactions,
            "criminal_history": history,
            "resolved_associates": resolved_associates,
            "life_timeline": timeline,
            "stats": {
                "total_incidents": len(incidents),
                "total_cdr": len(cdr),
                "calls_made": calls_made,
                "calls_received": calls_received,
                "total_transactions": len(transactions),
                "total_sent": total_sent,
                "total_received": total_received,
                "suspicious_transactions": suspicious_txns,
                "total_criminal_records": len(history),
                "total_associates": len(resolved_associates)
            }
        }

    def add_suspect(self, data):
        """Dynamically add a new suspect to the dataset and update the index."""
        # Determine unique ID
        if not data.get("id"):
            existing = [int(s.get("id", "SUSP_0").split("_")[-1]) for s in self.suspects
                        if s.get("id", "").startswith("SUSP_") and s.get("id", "").split("_")[-1].isdigit()]
            next_num = max(existing, default=0) + 1
            data["id"] = f"SUSP_{next_num:03d}"

        sid = data["id"]
        # Format lists
        if isinstance(data.get("known_associates"), str):
            data["known_associates"] = [a.strip() for a in data["known_associates"].split(",") if a.strip()]
        elif not data.get("known_associates"):
            data["known_associates"] = []

        if isinstance(data.get("vehicles"), str):
            data["vehicles"] = [v.strip() for v in data["vehicles"].split(",") if v.strip()]
        elif not data.get("vehicles"):
            data["vehicles"] = []

        self.suspects.append(data)

        # Index person
        self.entity_index["persons"][sid] = {
            "id": sid,
            "name": data.get("name", "Unknown Suspect"),
            "type": "PERSON",
            "phone": data.get("phone", ""),
            "phone2": data.get("phone2", ""),
            "organization": data.get("organization", ""),
            "address": data.get("address", ""),
            "risk_level": data.get("risk_level", "MEDIUM"),
            "age": int(data.get("age", 30)) if str(data.get("age", "")).isdigit() else 30,
            "gender": data.get("gender", "Male"),
            "incidents": [],
            "calls_made": 0,
            "calls_received": 0,
            "total_sent": 0,
            "total_received": 0,
            "criminal_records": int(data.get("prior_records", 0)) if str(data.get("prior_records", "")).isdigit() else 0,
            "known_associates": data.get("known_associates", []),
            "vehicles": data.get("vehicles", [])
        }

        # Index phone
        if data.get("phone"):
            self.entity_index["phones"][data["phone"]] = sid

        # Index organization
        org = data.get("organization")
        if org:
            if org not in self.entity_index["organizations"]:
                self.entity_index["organizations"][org] = {"name": org, "type": "ORGANIZATION", "members": []}
            if sid not in self.entity_index["organizations"][org]["members"]:
                self.entity_index["organizations"][org]["members"].append(sid)

        # Index location
        loc = data.get("address")
        if loc:
            if loc not in self.entity_index["locations"]:
                self.entity_index["locations"][loc] = {"name": loc, "type": "LOCATION", "associated_persons": []}
            if sid not in self.entity_index["locations"][loc]["associated_persons"]:
                self.entity_index["locations"][loc]["associated_persons"].append(sid)

        return self.entity_index["persons"][sid]

    def add_incident(self, data):
        """Dynamically add a new crime incident and link suspects."""
        if not data.get("incident_id"):
            existing = [int(i.get("incident_id", "INC_0").split("_")[-1]) for i in self.incidents
                        if i.get("incident_id", "").startswith("INC_") and i.get("incident_id", "").split("_")[-1].isdigit()]
            next_num = max(existing, default=0) + 1
            data["incident_id"] = f"INC_{next_num:04d}"

        iid = data["incident_id"]
        self.incidents.append(data)

        # Link suspects
        for key in ["suspect1_id", "suspect2_id"]:
            sid = str(data.get(key, ""))
            if sid in self.entity_index["persons"]:
                if iid not in self.entity_index["persons"][sid]["incidents"]:
                    self.entity_index["persons"][sid]["incidents"].append(iid)

        # Link location
        loc = data.get("location")
        if loc:
            if loc not in self.entity_index["locations"]:
                self.entity_index["locations"][loc] = {"name": loc, "type": "LOCATION", "associated_persons": []}
            for key in ["suspect1_id", "suspect2_id"]:
                sid = str(data.get(key, ""))
                if sid and sid not in self.entity_index["locations"][loc]["associated_persons"]:
                    self.entity_index["locations"][loc]["associated_persons"].append(sid)

        return data

