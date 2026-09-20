"""
Pattern Detection Module
Detects suspicious patterns, anomalies, and trends in criminal data.
Uses statistical methods, DBSCAN clustering, and time-series analysis.
"""

from collections import defaultdict
import math


class PatternDetector:
    """Detects suspicious patterns and anomalies in criminal data."""

    def __init__(self):
        self.patterns = []

    def analyze_all(self, data_processor):
        """Run all pattern detection analyses."""
        self.patterns = []

        self._detect_temporal_spikes(data_processor)
        self._detect_communication_bursts(data_processor)
        self._detect_financial_anomalies(data_processor)
        self._detect_geographic_clusters(data_processor)
        self._detect_repeat_offenders(data_processor)
        self._detect_network_patterns(data_processor)

        # Sort by severity
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        self.patterns.sort(key=lambda x: severity_order.get(x.get("severity", "LOW"), 3))

        return self.patterns

    def _detect_temporal_spikes(self, dp):
        """Detect unusual spikes in incident frequency."""
        daily_counts = defaultdict(int)
        hourly_counts = defaultdict(int)

        for inc in dp.incidents:
            date = inc.get("date", "")
            time = inc.get("time", "")
            if date:
                daily_counts[date] += 1
            if time:
                hour = int(time.split(":")[0])
                hourly_counts[hour] += 1

        # Daily spike detection (z-score > 2)
        if daily_counts:
            values = list(daily_counts.values())
            mean = sum(values) / len(values)
            std = math.sqrt(sum((v - mean) ** 2 for v in values) / max(len(values), 1))

            for date, count in daily_counts.items():
                if std > 0:
                    z_score = (count - mean) / std
                    if z_score > 2:
                        self.patterns.append({
                            "type": "TEMPORAL_SPIKE",
                            "severity": "HIGH" if z_score > 3 else "MEDIUM",
                            "title": f"Unusual crime spike on {date}",
                            "description": f"{count} incidents recorded (avg: {mean:.1f}, "
                                           f"z-score: {z_score:.2f}). This is {z_score:.1f}x "
                                           f"standard deviations above normal.",
                            "date": date,
                            "metric": count,
                            "z_score": round(z_score, 2),
                            "category": "Temporal Analysis"
                        })

        # Suspicious late-night activity (11 PM - 4 AM)
        late_night = sum(hourly_counts.get(h, 0) for h in [23, 0, 1, 2, 3, 4])
        total = sum(hourly_counts.values()) or 1
        if late_night / total > 0.25:
            self.patterns.append({
                "type": "LATE_NIGHT_ACTIVITY",
                "severity": "MEDIUM",
                "title": "High late-night criminal activity",
                "description": f"{late_night} incidents ({late_night/total*100:.1f}%) "
                               f"occurred between 11 PM - 4 AM.",
                "metric": late_night,
                "percentage": round(late_night / total * 100, 1),
                "category": "Temporal Analysis"
            })

    def _detect_communication_bursts(self, dp):
        """Detect unusual communication patterns in CDR data."""
        # Count calls per pair per day
        pair_daily = defaultdict(lambda: defaultdict(int))
        pair_total = defaultdict(int)

        for cdr in dp.cdr_records:
            c = str(cdr.get("caller_id", ""))
            r = str(cdr.get("receiver_id", ""))
            date = cdr.get("date", "")
            if c and r and c != r:
                key = tuple(sorted([c, r]))
                pair_daily[key][date] += 1
                pair_total[key] += 1

        # Find pairs with abnormal communication frequency
        for pair, daily in pair_daily.items():
            max_calls_day = max(daily.values()) if daily else 0
            avg_calls = sum(daily.values()) / max(len(daily), 1)

            if max_calls_day >= 10:
                # Resolve names
                names = []
                for pid in pair:
                    person = dp.entity_index["persons"].get(pid)
                    names.append(person["name"] if person else pid)

                self.patterns.append({
                    "type": "COMMUNICATION_BURST",
                    "severity": "HIGH" if max_calls_day >= 20 else "MEDIUM",
                    "title": f"Communication burst: {names[0]} ↔ {names[1]}",
                    "description": f"Peak of {max_calls_day} communications in a single day "
                                   f"(avg: {avg_calls:.1f}/day). Total: {pair_total[pair]} records.",
                    "entities": list(pair),
                    "entity_names": names,
                    "peak_calls": max_calls_day,
                    "total_calls": pair_total[pair],
                    "category": "Communication Analysis"
                })

    def _detect_financial_anomalies(self, dp):
        """Detect suspicious financial patterns."""
        # Large transactions
        large_txns = []
        person_totals = defaultdict(lambda: {"sent": 0, "received": 0, "count": 0})
        structuring_suspects = defaultdict(list)

        for txn in dp.financial_records:
            amount = float(txn.get("amount", 0))
            sender = str(txn.get("sender_id", ""))
            receiver = str(txn.get("receiver_id", ""))
            date = txn.get("date", "")
            txn_type = txn.get("transaction_type", "")

            person_totals[sender]["sent"] += amount
            person_totals[sender]["count"] += 1
            person_totals[receiver]["received"] += amount

            # Flag very large transactions
            if amount >= 2000000:
                s_person = dp.entity_index["persons"].get(sender, {})
                r_person = dp.entity_index["persons"].get(receiver, {})
                large_txns.append({
                    "amount": amount,
                    "sender": s_person.get("name", sender),
                    "receiver": r_person.get("name", receiver),
                    "date": date,
                    "type": txn_type
                })

            # Structuring detection (multiple txns just under reporting threshold)
            if 400000 <= amount <= 500000:
                structuring_suspects[sender].append({
                    "amount": amount, "date": date
                })

        # Report large transactions
        for txn in large_txns[:5]:
            self.patterns.append({
                "type": "LARGE_TRANSACTION",
                "severity": "HIGH",
                "title": f"Large transaction: ₹{txn['amount']:,.0f}",
                "description": f"{txn['sender']} → {txn['receiver']} via {txn['type']} "
                               f"on {txn['date']}. Amount exceeds ₹20L threshold.",
                "amount": txn["amount"],
                "category": "Financial Analysis"
            })

        # Report structuring suspects
        for person_id, txns in structuring_suspects.items():
            if len(txns) >= 3:
                person = dp.entity_index["persons"].get(person_id, {})
                total = sum(t["amount"] for t in txns)
                self.patterns.append({
                    "type": "STRUCTURING",
                    "severity": "CRITICAL",
                    "title": f"Possible structuring: {person.get('name', person_id)}",
                    "description": f"{len(txns)} transactions just below reporting threshold "
                                   f"(₹4-5L each). Total: ₹{total:,.0f}. "
                                   f"Classic money laundering pattern.",
                    "entity": person_id,
                    "transaction_count": len(txns),
                    "total_amount": total,
                    "category": "Financial Analysis"
                })

        # Persons with disproportionate flows
        for person_id, totals in person_totals.items():
            if totals["sent"] > 5000000 or totals["received"] > 5000000:
                person = dp.entity_index["persons"].get(person_id, {})
                self.patterns.append({
                    "type": "HIGH_VOLUME_TRANSACTOR",
                    "severity": "MEDIUM",
                    "title": f"High-volume transactor: {person.get('name', person_id)}",
                    "description": f"Total sent: ₹{totals['sent']:,.0f}, "
                                   f"received: ₹{totals['received']:,.0f} "
                                   f"across {totals['count']} transactions.",
                    "entity": person_id,
                    "total_sent": totals["sent"],
                    "total_received": totals["received"],
                    "category": "Financial Analysis"
                })

    def _detect_geographic_clusters(self, dp):
        """Detect geographic crime hotspots."""
        location_crimes = defaultdict(lambda: {"count": 0, "types": defaultdict(int)})

        for inc in dp.incidents:
            loc = inc.get("location", "")
            crime = inc.get("crime_type", "")
            if loc:
                location_crimes[loc]["count"] += 1
                location_crimes[loc]["types"][crime] += 1

        # Flag locations with high crime concentration
        total_incidents = len(dp.incidents) or 1
        for loc, data in location_crimes.items():
            concentration = data["count"] / total_incidents * 100
            if data["count"] >= 15:
                top_crime = max(data["types"].items(), key=lambda x: x[1])
                self.patterns.append({
                    "type": "CRIME_HOTSPOT",
                    "severity": "HIGH" if data["count"] >= 25 else "MEDIUM",
                    "title": f"Crime hotspot: {loc}",
                    "description": f"{data['count']} incidents ({concentration:.1f}% of total). "
                                   f"Dominant crime: {top_crime[0]} ({top_crime[1]} cases).",
                    "location": loc,
                    "incident_count": data["count"],
                    "concentration": round(concentration, 1),
                    "crime_breakdown": dict(data["types"]),
                    "category": "Geographic Analysis"
                })

    def _detect_repeat_offenders(self, dp):
        """Identify repeat offenders and escalation patterns."""
        person_crimes = defaultdict(list)

        for inc in dp.incidents:
            for key in ["suspect1_id", "suspect2_id"]:
                pid = str(inc.get(key, ""))
                if pid:
                    person_crimes[pid].append({
                        "date": inc.get("date", ""),
                        "crime_type": inc.get("crime_type", ""),
                        "location": inc.get("location", "")
                    })

        for pid, crimes in person_crimes.items():
            if len(crimes) >= 8:
                person = dp.entity_index["persons"].get(pid, {})
                crime_types = set(c["crime_type"] for c in crimes)

                severity = "CRITICAL" if len(crimes) >= 15 else "HIGH"
                self.patterns.append({
                    "type": "REPEAT_OFFENDER",
                    "severity": severity,
                    "title": f"Repeat offender: {person.get('name', pid)}",
                    "description": f"Linked to {len(crimes)} incidents involving "
                                   f"{len(crime_types)} different crime types. "
                                   f"Types: {', '.join(list(crime_types)[:5])}.",
                    "entity": pid,
                    "entity_name": person.get("name", pid),
                    "incident_count": len(crimes),
                    "crime_types": list(crime_types),
                    "category": "Behavioral Analysis"
                })

    def _detect_network_patterns(self, dp):
        """Detect suspicious network-level patterns."""
        # Find persons connected to multiple organizations
        org_members = defaultdict(set)
        for s in dp.suspects:
            org = s.get("organization", "")
            if org:
                org_members[org].add(s.get("id", ""))

        # Find bridge persons (in multiple orgs via associates)
        person_orgs = defaultdict(set)
        for s in dp.suspects:
            pid = s.get("id", "")
            own_org = s.get("organization", "")
            if own_org:
                person_orgs[pid].add(own_org)

            associates = s.get("known_associates", [])
            if isinstance(associates, str):
                try:
                    import json
                    associates = json.loads(associates)
                except Exception:
                    associates = []

            for assoc_id in associates:
                assoc = next((x for x in dp.suspects if x.get("id") == assoc_id), None)
                if assoc and assoc.get("organization"):
                    person_orgs[pid].add(assoc["organization"])

        for pid, orgs in person_orgs.items():
            if len(orgs) >= 3:
                person = dp.entity_index["persons"].get(pid, {})
                self.patterns.append({
                    "type": "INTER_ORG_BROKER",
                    "severity": "CRITICAL",
                    "title": f"Inter-org broker: {person.get('name', pid)}",
                    "description": f"Connected to {len(orgs)} organizations: "
                                   f"{', '.join(list(orgs)[:5])}. "
                                   f"Potential intermediary or facilitator.",
                    "entity": pid,
                    "entity_name": person.get("name", pid),
                    "organizations": list(orgs),
                    "category": "Network Analysis"
                })

    def get_patterns_summary(self):
        """Get a summary of detected patterns by category."""
        summary = defaultdict(lambda: {"count": 0, "critical": 0, "high": 0})
        for p in self.patterns:
            cat = p.get("category", "Other")
            summary[cat]["count"] += 1
            if p.get("severity") == "CRITICAL":
                summary[cat]["critical"] += 1
            elif p.get("severity") == "HIGH":
                summary[cat]["high"] += 1

        return {
            "total_patterns": len(self.patterns),
            "critical_count": sum(1 for p in self.patterns if p.get("severity") == "CRITICAL"),
            "high_count": sum(1 for p in self.patterns if p.get("severity") == "HIGH"),
            "medium_count": sum(1 for p in self.patterns if p.get("severity") == "MEDIUM"),
            "low_count": sum(1 for p in self.patterns if p.get("severity") == "LOW"),
            "by_category": dict(summary),
        }
