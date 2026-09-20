#!/usr/bin/env python3
"""
AI-Powered Criminal Network Analysis System
Main Flask Application
"""

import os
import sys
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.data_processor import DataProcessor
from modules.nlp_engine import NLPEngine
from modules.graph_engine import GraphEngine
from modules.prediction_engine import PredictionEngine
from modules.pattern_detector import PatternDetector

# ── Flask App ─────────────────────────────────────────────────
app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

# ── Initialize Engines ────────────────────────────────────────
print("=" * 60)
print("🔍 AI-Powered Criminal Network Analysis System")
print("=" * 60)

data_processor = DataProcessor(data_dir="data")
nlp_engine = NLPEngine()
graph_engine = GraphEngine()
prediction_engine = PredictionEngine(models_dir="models", models2_dir="models 2")
pattern_detector = PatternDetector()

# Load data and build graph
data_processor.load_all()
graph_engine.build_graph(data_processor)
patterns = pattern_detector.analyze_all(data_processor)
print(f"  🔎 {len(patterns)} suspicious patterns detected")

# Load ML models (optional — may take time)
LOAD_ML_MODELS = os.environ.get("LOAD_ML_MODELS", "false").lower() == "true"
if LOAD_ML_MODELS:
    prediction_engine.load_models()
else:
    print("  ℹ️  ML models not loaded (set LOAD_ML_MODELS=true to enable)")
    print("     Using heuristic fallback for predictions")

print("=" * 60)
print("🚀 System ready!")
print("=" * 60)


# ── Serve Frontend ────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("static", "index.html")


# ── Dashboard API ─────────────────────────────────────────────
@app.route("/api/dashboard")
def api_dashboard():
    stats = data_processor.get_dashboard_stats()
    network_stats = graph_engine.get_network_stats()
    pattern_summary = pattern_detector.get_patterns_summary()
    return jsonify({
        "stats": stats,
        "network": network_stats,
        "patterns": pattern_summary,
        "models": prediction_engine.get_model_info(),
    })


# ── Network Graph API ─────────────────────────────────────────
@app.route("/api/network")
def api_network():
    graph_data = graph_engine.get_graph_data()
    return jsonify(graph_data)


@app.route("/api/network/communities")
def api_communities():
    communities = graph_engine.get_communities_data()
    return jsonify({"communities": communities})


@app.route("/api/network/influencers")
def api_influencers():
    top_n = request.args.get("top", 20, type=int)
    influencers = graph_engine.get_influencers(top_n=top_n)
    return jsonify({"influencers": influencers})


@app.route("/api/network/path")
def api_shortest_path():
    source = request.args.get("source", "")
    target = request.args.get("target", "")
    if not source or not target:
        return jsonify({"error": "source and target parameters required"}), 400
    result = graph_engine.get_shortest_path(source, target)
    return jsonify(result)


# ── Entity API ─────────────────────────────────────────────────
@app.route("/api/entities")
def api_entities():
    query = request.args.get("q", "")
    if query:
        results = data_processor.search_entities(query)
        return jsonify({"results": results, "query": query})
    else:
        all_entities = data_processor.get_all_entities()
        persons = data_processor.get_all_persons()
        # Return summary + first 50 persons
        return jsonify({
            "summary": all_entities,
            "persons": sorted(persons, key=lambda x: x.get("risk_level", "LOW") == "CRITICAL",
                              reverse=True)[:100]
        })


@app.route("/api/entity/<entity_id>")
def api_entity_detail(entity_id):
    person = data_processor.get_person(entity_id)
    if not person:
        return jsonify({"error": "Entity not found"}), 404

    incidents = data_processor.get_incidents_for_person(entity_id)
    cdr = data_processor.get_cdr_for_person(entity_id)
    transactions = data_processor.get_transactions_for_person(entity_id)
    history = data_processor.get_history_for_person(entity_id)

    return jsonify({
        "entity": person,
        "incidents": incidents[:50],
        "cdr_records": cdr[:50],
        "transactions": transactions[:50],
        "criminal_history": history,
    })


# ── Add Suspect / Crime Ingestion API ─────────────────────────
@app.route("/api/suspects/add", methods=["POST"])
def api_add_suspect():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "Suspect name is required"}), 400

    new_suspect = data_processor.add_suspect(data)
    graph_engine.add_person_node(new_suspect)
    # Refresh pattern analysis
    pattern_detector.analyze_all(data_processor)

    return jsonify({
        "success": True,
        "message": f"Suspect '{new_suspect['name']}' ({new_suspect['id']}) added to intelligence graph",
        "suspect": new_suspect
    }), 201


@app.route("/api/incidents/add", methods=["POST"])
def api_add_incident():
    data = request.get_json()
    if not data or not data.get("crime_type"):
        return jsonify({"error": "Crime type is required"}), 400

    new_incident = data_processor.add_incident(data)
    graph_engine.add_incident_edge(new_incident)
    # Refresh pattern analysis
    pattern_detector.analyze_all(data_processor)

    return jsonify({
        "success": True,
        "message": f"Incident '{new_incident['incident_id']}' logged successfully",
        "incident": new_incident
    }), 201


# ── Prediction API ────────────────────────────────────────────
@app.route("/api/predict/crime-type", methods=["POST"])
def api_predict_crime():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    result = prediction_engine.predict_crime_type(
        hour=int(data.get("hour", 12)),
        day_of_week=int(data.get("day_of_week", 0)),
        month=int(data.get("month", 1)),
        beat=int(data.get("beat", 1000)),
        district=int(data.get("district", 1)),
        community_area=int(data.get("community_area", 1)),
        location_description=str(data.get("location_description", "STREET")),
    )
    return jsonify(result)


@app.route("/api/predict/arrest", methods=["POST"])
def api_predict_arrest():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    result = prediction_engine.predict_arrest(
        hour=int(data.get("hour", 12)),
        day_of_week=int(data.get("day_of_week", 0)),
        month=int(data.get("month", 1)),
        beat=int(data.get("beat", 1000)),
        district=int(data.get("district", 1)),
        community_area=int(data.get("community_area", 1)),
        primary_type=str(data.get("primary_type", "THEFT")),
        location_description=str(data.get("location_description", "STREET")),
    )
    return jsonify(result)


# ── Pattern Detection API ─────────────────────────────────────
@app.route("/api/patterns")
def api_patterns():
    severity = request.args.get("severity", "")
    category = request.args.get("category", "")

    filtered = pattern_detector.patterns
    if severity:
        filtered = [p for p in filtered if p.get("severity") == severity.upper()]
    if category:
        filtered = [p for p in filtered if p.get("category", "").lower() == category.lower()]

    return jsonify({
        "patterns": filtered,
        "summary": pattern_detector.get_patterns_summary()
    })


# ── Timeline API ──────────────────────────────────────────────
@app.route("/api/timeline")
def api_timeline():
    person_id = request.args.get("person_id", None)
    events = data_processor.get_timeline(person_id)
    return jsonify({"events": events})


# ── NLP Analysis API ──────────────────────────────────────────
@app.route("/api/analyze-text", methods=["POST"])
def api_analyze_text():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "JSON body with 'text' field required"}), 400

    text = data["text"]
    analysis = nlp_engine.analyze_text(text)
    relationships = nlp_engine.extract_relationships_from_text(text)
    analysis["relationships"] = relationships

    return jsonify(analysis)


# ── NLP Batch Extraction ──────────────────────────────────────
@app.route("/api/entities/extracted")
def api_extracted_entities():
    """Extract entities from all incident narratives."""
    narratives = [inc.get("narrative", "") for inc in data_processor.incidents if inc.get("narrative")]
    entities = nlp_engine.extract_entities_batch(narratives[:200])
    return jsonify({"extracted_entities": entities})


# ── Model Info API ─────────────────────────────────────────────
@app.route("/api/models")
def api_models():
    return jsonify({"models": prediction_engine.get_model_info()})


# ── Run ───────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"\n🌐 Starting server on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
