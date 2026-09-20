"""
Graph Network Analysis Engine
Builds and analyzes criminal relationship graphs using NetworkX.
Detects communities, influencers, and suspicious connection patterns.
"""

import networkx as nx
from collections import defaultdict

try:
    import community as community_louvain
    _LOUVAIN_AVAILABLE = True
except ImportError:
    _LOUVAIN_AVAILABLE = False


class GraphEngine:
    """Criminal network graph analysis engine."""

    def __init__(self):
        self.G = nx.Graph()
        self._communities = None
        self._centrality_cache = {}

    def build_graph(self, data_processor):
        """
        Build a multi-relational graph from all data sources.
        Nodes: persons, organizations, locations, phones
        Edges: communication, financial, co-occurrence, association
        """
        self.G = nx.Graph()
        dp = data_processor

        # ── Add Person Nodes ──────────────────────────────────
        for person in dp.get_all_persons():
            pid = person["id"]
            self.G.add_node(pid, **{
                "label": person["name"],
                "type": "PERSON",
                "risk_level": person.get("risk_level", "LOW"),
                "organization": person.get("organization", ""),
                "phone": person.get("phone", ""),
                "incidents": len(person.get("incidents", [])),
                "criminal_records": person.get("criminal_records", 0),
            })

        # ── Add Organization Nodes ────────────────────────────
        for org in dp.get_organizations():
            org_id = f"ORG:{org['name']}"
            self.G.add_node(org_id, **{
                "label": org["name"],
                "type": "ORGANIZATION",
                "members": len(org.get("members", [])),
            })
            # Connect members to organization
            for member_id in org.get("members", []):
                if self.G.has_node(member_id):
                    self.G.add_edge(member_id, org_id,
                                   relation="MEMBER_OF", weight=3)

        # ── Add Known Associate Edges ─────────────────────────
        for person in dp.suspects:
            pid = person.get("id", "")
            associates = person.get("known_associates", [])
            if isinstance(associates, str):
                try:
                    import json
                    associates = json.loads(associates)
                except Exception:
                    associates = []
            for assoc_id in associates:
                if self.G.has_node(pid) and self.G.has_node(assoc_id):
                    if self.G.has_edge(pid, assoc_id):
                        self.G[pid][assoc_id]["weight"] += 2
                    else:
                        self.G.add_edge(pid, assoc_id,
                                        relation="KNOWN_ASSOCIATE", weight=2)

        # ── Add Incident Co-occurrence Edges ──────────────────
        incident_pairs = defaultdict(int)
        for inc in dp.incidents:
            s1 = str(inc.get("suspect1_id", ""))
            s2 = str(inc.get("suspect2_id", ""))
            if s1 and s2 and s1 != s2:
                key = tuple(sorted([s1, s2]))
                incident_pairs[key] += 1

        for (s1, s2), count in incident_pairs.items():
            if self.G.has_node(s1) and self.G.has_node(s2):
                if self.G.has_edge(s1, s2):
                    self.G[s1][s2]["weight"] += count
                    self.G[s1][s2]["co_incidents"] = count
                else:
                    self.G.add_edge(s1, s2,
                                    relation="CO_INCIDENT",
                                    weight=count,
                                    co_incidents=count)

        # ── Add CDR Communication Edges ───────────────────────
        call_pairs = defaultdict(int)
        for cdr in dp.cdr_records:
            c = str(cdr.get("caller_id", ""))
            r = str(cdr.get("receiver_id", ""))
            if c and r and c != r:
                key = tuple(sorted([c, r]))
                call_pairs[key] += 1

        for (c, r), count in call_pairs.items():
            if self.G.has_node(c) and self.G.has_node(r):
                if self.G.has_edge(c, r):
                    self.G[c][r]["weight"] += min(count / 10, 5)
                    self.G[c][r]["call_count"] = count
                else:
                    self.G.add_edge(c, r,
                                    relation="COMMUNICATION",
                                    weight=min(count / 10, 5),
                                    call_count=count)

        # ── Add Financial Transaction Edges ───────────────────
        txn_pairs = defaultdict(lambda: {"count": 0, "total_amount": 0})
        for txn in dp.financial_records:
            s = str(txn.get("sender_id", ""))
            r = str(txn.get("receiver_id", ""))
            if s and r and s != r:
                key = tuple(sorted([s, r]))
                txn_pairs[key]["count"] += 1
                txn_pairs[key]["total_amount"] += float(txn.get("amount", 0))

        for (s, r), info in txn_pairs.items():
            if self.G.has_node(s) and self.G.has_node(r):
                if self.G.has_edge(s, r):
                    self.G[s][r]["weight"] += min(info["total_amount"] / 1000000, 5)
                    self.G[s][r]["txn_count"] = info["count"]
                    self.G[s][r]["txn_amount"] = info["total_amount"]
                else:
                    self.G.add_edge(s, r,
                                    relation="FINANCIAL",
                                    weight=min(info["total_amount"] / 1000000, 5),
                                    txn_count=info["count"],
                                    txn_amount=info["total_amount"])

        # Clear caches
        self._communities = None
        self._centrality_cache = {}

        print(f"  ✅ Graph built: {self.G.number_of_nodes()} nodes, {self.G.number_of_edges()} edges")

    def get_graph_data(self):
        """Get graph data formatted for vis.js visualization."""
        nodes = []
        edges = []

        # Get centrality for sizing
        degree_cent = nx.degree_centrality(self.G)
        communities = self.detect_communities()

        # Color palette for communities
        community_colors = [
            "#FF6B6B", "#059669", "#45B7D1", "#96CEB4", "#FFEAA7",
            "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
            "#F0B27A", "#AED6F1", "#A3E4D7", "#FAD7A0", "#D2B4DE",
            "#A9CCE3", "#A9DFBF", "#F9E79F", "#FADBD8", "#D5F5E3"
        ]

        for node_id in self.G.nodes():
            node_data = self.G.nodes[node_id]
            node_type = node_data.get("type", "UNKNOWN")
            comm_id = communities.get(node_id, 0)

            # Determine node appearance
            if node_type == "PERSON":
                color = community_colors[comm_id % len(community_colors)]
                shape = "dot"
                size = 10 + degree_cent.get(node_id, 0) * 80
                risk = node_data.get("risk_level", "LOW")
                if risk == "CRITICAL":
                    border_color = "#FF0000"
                    border_width = 3
                elif risk == "HIGH":
                    border_color = "#FF6600"
                    border_width = 2
                else:
                    border_color = color
                    border_width = 1
            elif node_type == "ORGANIZATION":
                color = "#FFD700"
                shape = "diamond"
                size = 20
                border_color = "#DAA520"
                border_width = 2
            else:
                color = "#888888"
                shape = "square"
                size = 12
                border_color = "#666666"
                border_width = 1

            nodes.append({
                "id": node_id,
                "label": node_data.get("label", node_id),
                "title": self._build_tooltip(node_id, node_data, degree_cent),
                "color": {
                    "background": color,
                    "border": border_color,
                    "highlight": {"background": "#FFFFFF", "border": border_color}
                },
                "shape": shape,
                "size": size,
                "borderWidth": border_width,
                "type": node_type,
                "community": comm_id,
                "risk_level": node_data.get("risk_level", ""),
                "centrality": round(degree_cent.get(node_id, 0), 4),
            })

        for u, v, data in self.G.edges(data=True):
            relation = data.get("relation", "UNKNOWN")
            weight = data.get("weight", 1)

            # Edge color by relationship type
            edge_colors = {
                "KNOWN_ASSOCIATE": "#FF6B6B",
                "CO_INCIDENT": "#FF9800",
                "COMMUNICATION": "#059669",
                "FINANCIAL": "#FFD700",
                "MEMBER_OF": "#9B59B6",
            }

            edges.append({
                "from": u,
                "to": v,
                "color": {"color": edge_colors.get(relation, "#888888"), "opacity": 0.6},
                "width": max(1, min(weight, 8)),
                "title": f"{relation} (weight: {weight:.1f})",
                "relation": relation,
                "smooth": {"type": "continuous"},
            })

        return {"nodes": nodes, "edges": edges}

    def _build_tooltip(self, node_id, data, degree_cent):
        """Build HTML tooltip for a node."""
        lines = [f"<b>{data.get('label', node_id)}</b>"]
        lines.append(f"Type: {data.get('type', 'Unknown')}")
        if data.get('risk_level'):
            lines.append(f"Risk: {data['risk_level']}")
        if data.get('organization'):
            lines.append(f"Org: {data['organization']}")
        lines.append(f"Connections: {self.G.degree(node_id)}")
        lines.append(f"Centrality: {degree_cent.get(node_id, 0):.4f}")
        if data.get('incidents'):
            lines.append(f"Incidents: {data['incidents']}")
        if data.get('criminal_records'):
            lines.append(f"Criminal Records: {data['criminal_records']}")
        return "<br>".join(lines)

    def detect_communities(self):
        """Detect criminal communities using Louvain algorithm."""
        if self._communities is not None:
            return self._communities

        # Work with person-only subgraph for community detection
        person_nodes = [n for n, d in self.G.nodes(data=True) if d.get("type") == "PERSON"]
        subgraph = self.G.subgraph(person_nodes).copy()

        if _LOUVAIN_AVAILABLE and len(subgraph.nodes()) > 0:
            try:
                partition = community_louvain.best_partition(subgraph, resolution=1.0)
                # Assign communities to all nodes
                self._communities = {}
                for node in self.G.nodes():
                    self._communities[node] = partition.get(node, -1)
            except Exception:
                self._communities = {n: 0 for n in self.G.nodes()}
        else:
            # Fallback: use connected components
            self._communities = {}
            for i, component in enumerate(nx.connected_components(subgraph)):
                for node in component:
                    self._communities[node] = i
            for node in self.G.nodes():
                if node not in self._communities:
                    self._communities[node] = -1

        return self._communities

    def get_communities_data(self):
        """Get detailed community information."""
        communities = self.detect_communities()
        community_data = defaultdict(lambda: {
            "members": [], "total_incidents": 0,
            "risk_profile": defaultdict(int), "organizations": set()
        })

        for node_id, comm_id in communities.items():
            if comm_id < 0:
                continue
            node_data = self.G.nodes.get(node_id, {})
            if node_data.get("type") != "PERSON":
                continue

            community_data[comm_id]["members"].append({
                "id": node_id,
                "name": node_data.get("label", node_id),
                "risk_level": node_data.get("risk_level", "LOW"),
                "connections": self.G.degree(node_id)
            })
            community_data[comm_id]["total_incidents"] += node_data.get("incidents", 0)
            community_data[comm_id]["risk_profile"][node_data.get("risk_level", "LOW")] += 1
            if node_data.get("organization"):
                community_data[comm_id]["organizations"].add(node_data["organization"])

        result = []
        for comm_id, data in sorted(community_data.items()):
            if len(data["members"]) < 2:
                continue
            data["organizations"] = list(data["organizations"])
            data["risk_profile"] = dict(data["risk_profile"])
            data["id"] = comm_id
            data["size"] = len(data["members"])

            # Determine overall threat level
            risk = data["risk_profile"]
            if risk.get("CRITICAL", 0) > 0:
                data["threat_level"] = "CRITICAL"
            elif risk.get("HIGH", 0) >= 2:
                data["threat_level"] = "HIGH"
            elif risk.get("MEDIUM", 0) >= 2:
                data["threat_level"] = "MEDIUM"
            else:
                data["threat_level"] = "LOW"

            result.append(data)

        result.sort(key=lambda x: x["size"], reverse=True)
        return result

    def get_influencers(self, top_n=20):
        """Identify key influencers using multiple centrality metrics."""
        if not self.G.nodes():
            return []

        person_nodes = [n for n, d in self.G.nodes(data=True) if d.get("type") == "PERSON"]
        subgraph = self.G.subgraph(person_nodes)

        degree_cent = nx.degree_centrality(subgraph)
        betweenness_cent = nx.betweenness_centrality(subgraph, weight="weight")
        closeness_cent = nx.closeness_centrality(subgraph)

        try:
            pagerank = nx.pagerank(subgraph, weight="weight")
        except Exception:
            pagerank = {n: 0 for n in subgraph.nodes()}

        # Composite influence score
        influencers = []
        for node_id in person_nodes:
            node_data = self.G.nodes[node_id]
            composite = (
                degree_cent.get(node_id, 0) * 0.25 +
                betweenness_cent.get(node_id, 0) * 0.35 +
                closeness_cent.get(node_id, 0) * 0.15 +
                pagerank.get(node_id, 0) * 0.25
            )

            influencers.append({
                "id": node_id,
                "name": node_data.get("label", node_id),
                "risk_level": node_data.get("risk_level", "LOW"),
                "organization": node_data.get("organization", ""),
                "degree_centrality": round(degree_cent.get(node_id, 0), 4),
                "betweenness_centrality": round(betweenness_cent.get(node_id, 0), 4),
                "closeness_centrality": round(closeness_cent.get(node_id, 0), 4),
                "pagerank": round(pagerank.get(node_id, 0), 6),
                "composite_score": round(composite, 4),
                "connections": self.G.degree(node_id),
                "incidents": node_data.get("incidents", 0),
                "criminal_records": node_data.get("criminal_records", 0),
            })

        influencers.sort(key=lambda x: x["composite_score"], reverse=True)
        return influencers[:top_n]

    def get_shortest_path(self, source, target):
        """Find shortest path between two entities."""
        try:
            path = nx.shortest_path(self.G, source, target)
            path_details = []
            for i, node_id in enumerate(path):
                node_data = self.G.nodes.get(node_id, {})
                detail = {
                    "id": node_id,
                    "name": node_data.get("label", node_id),
                    "type": node_data.get("type", "UNKNOWN"),
                }
                if i < len(path) - 1:
                    edge_data = self.G.edges.get((path[i], path[i+1]), {})
                    detail["edge_to_next"] = {
                        "relation": edge_data.get("relation", "UNKNOWN"),
                        "weight": edge_data.get("weight", 0)
                    }
                path_details.append(detail)
            return {
                "found": True,
                "length": len(path) - 1,
                "path": path_details
            }
        except nx.NetworkXNoPath:
            return {"found": False, "message": "No path exists between these entities"}
        except nx.NodeNotFound as e:
            return {"found": False, "message": str(e)}

    def get_network_stats(self):
        """Get overall network statistics."""
        person_nodes = [n for n, d in self.G.nodes(data=True) if d.get("type") == "PERSON"]
        org_nodes = [n for n, d in self.G.nodes(data=True) if d.get("type") == "ORGANIZATION"]
        subgraph = self.G.subgraph(person_nodes)

        stats = {
            "total_nodes": self.G.number_of_nodes(),
            "total_edges": self.G.number_of_edges(),
            "person_nodes": len(person_nodes),
            "organization_nodes": len(org_nodes),
            "density": round(nx.density(subgraph), 4) if person_nodes else 0,
            "connected_components": nx.number_connected_components(subgraph) if person_nodes else 0,
            "avg_degree": round(sum(dict(subgraph.degree()).values()) / max(len(person_nodes), 1), 2),
        }

        communities = self.get_communities_data()
        stats["communities_detected"] = len(communities)
        stats["largest_community_size"] = max((c["size"] for c in communities), default=0)

        return stats
