# 🔍 CrimeNet AI — AI-Powered Criminal Network Analysis System

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-000000.svg?style=flat&logo=flask&logoColor=white)](https://palletsprojects.com/p/flask/)
[![scikit-learn](https://img.shields.io/badge/ML-scikit--learn-F7931E.svg?style=flat&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![NetworkX](https://img.shields.io/badge/Graph-NetworkX-blue.svg?style=flat)](https://networkx.org/)
[![spaCy](https://img.shields.io/badge/NLP-spaCy-09A3D5.svg?style=flat&logo=spacy&logoColor=white)](https://spacy.io/)
[![vis.js](https://img.shields.io/badge/Graph%20UI-vis.js-orange.svg?style=flat)](https://visjs.org/)
[![Hackathon](https://img.shields.io/badge/Hackathon-KAYA-purple.svg?style=flat)](#)

> **Autonomous Multi-Source Intelligence Fusion & Graph Analytics Engine for Law Enforcement & Investigative Agencies.**

Developed for **KAYA Hackathon** by **Team Kaya**.

---

## 📌 Problem Statement

Modern organized criminal enterprises operate through intricate networks involving associates, shell companies, financial conduits, encrypted communication channels, and coordinated logistical events. Law enforcement agencies face significant investigative bottlenecks:

1. **Fragmented & Disparate Data Sources**: First Information Reports (FIRs), Call Detail Records (CDRs), suspicious financial transactions, surveillance logs, and criminal records reside in isolated data silos.
2. **Hidden Non-Obvious Relationships**: Traditional relational databases fail to capture multi-hop links between kingpins, mules, and intermediaries.
3. **Information Overload & Manual Delays**: Investigators manually pore over thousands of pages of unstructured text, leading to investigative blind spots and missed critical connections.

---

## 💡 Solution: CrimeNet AI

**CrimeNet AI** is an end-to-end intelligence platform that ingests multi-source unstructured and structured data, automatically constructs an interconnected **Criminal Knowledge Graph**, leverages **Machine Learning** models to predict crime types and arrest probabilities, and delivers actionable, real-time investigative intelligence through a high-performance interactive dashboard.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   Multi-Source Data Ingestion Pipeline                   │
│   [Police FIRs]  [CDR Records]  [Bank Transactions]  [Criminal Records]  │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                   AI & Intelligence Processing Core                      │
│  ┌──────────────────────┐  ┌─────────────────────┐  ┌─────────────────┐  │
│  │ NLP Entity Extraction│  │ Graph Engine        │  │ ML Predictors   │  │
│  │ (spaCy + Regex NER)  │  │ (NetworkX + Louvain)│  │ (Random Forest) │  │
│  │ Suspects, Orgs, Locs │  │ Centrality & Cliques│  │ Crime & Arrest  │  │
│  └──────────────────────┘  └─────────────────────┘  └─────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ Pattern & Anomaly Detection (Temporal, Financial, Repeat-Offender) │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │ REST APIs
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                Investigator Command Center (Web UI)                      │
│   Network Graph │ Communities │ Dossier │ Predictions │ Timeline │ NLP   │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Capabilities

### 1. 🕸️ Interactive Knowledge Graph & Social Network Analysis (SNA)
- **Force-Directed Graph Visualization**: Powered by `vis.js`, rendering suspects, organizations, locations, vehicles, and incidents.
- **Community Detection**: Implements the **Louvain modularity algorithm** to isolate hidden syndicates and sub-cells.
- **Key Player Identification**: Computes **Degree**, **Betweenness**, **Closeness**, and **PageRank** centrality metrics to identify kingpins, brokers, and operational nodes.
- **Shortest Path & Chain of Association**: Trace degrees of separation and communication/transaction chains between any two entities.

### 2. 🧠 Machine Learning Crime & Arrest Prediction
- Trained on **Chicago Crime Dataset (2023)** with scikit-learn Random Forests.
- **Multi-Class Crime Type Classifier**: Predicts crime categories based on temporal, spatial, and contextual indicators.
- **Arrest Probability Scoring**: Computes likelihood of apprehension given location type, domestic flags, and historical patterns.

### 3. 📝 NLP Unstructured Text & FIR Intelligence Parser
- Extracts entities (Suspects, Aliases, Organizations, Locations, Phone Numbers, Vehicles, Currency Amounts) using custom spaCy pipelines and regular expression pattern matchers.
- Dynamically integrates extracted entities and relationships directly into the live graph.

### 4. 🚨 Proactive Pattern & Anomaly Detection
- **Burst / Spike Analysis**: Identifies temporal surges in suspicious calls and financial movements.
- **Financial Smurfing & High-Value Alerts**: Flags rapid structuring and high-value cash transactions.
- **Cross-Jurisdiction & Repeat-Offender Tracking**: Flags recidivist targets operating across multiple districts.

### 5. ⏱️ Chronological Intelligence Timeline
- Synthesizes calls, financial movements, incidents, and arrests into a unified chronological event stream.

---

## 🗂️ Project Structure

```
KAYA-HACKTHON/
├── app.py                          # Flask application & REST API endpoints
├── requirements.txt                # Pinned production dependencies
├── README.md                       # Documentation & presentation guide
├── .gitignore                      # Git configuration (ignores large models & caches)
├── data/
│   ├── generate_synthetic_data.py  # Realistic multi-source data generator
│   ├── suspects.json               # Seed suspect profiles with aliases & metadata
│   ├── suspects.csv                # Tabular suspect registry
│   ├── incidents.csv               # Crime incidents & FIR reports
│   ├── cdr_records.csv             # Call Detail Records (calls & SMS logs)
│   ├── financial_transactions.csv  # Bank transfers & cash transactions
│   └── criminal_history.csv        # Historical conviction & charge records
├── modules/
│   ├── __init__.py                 # Python package initialization
│   ├── data_processor.py           # Ingestion, normalization & indexing pipeline
│   ├── nlp_engine.py               # spaCy NER & regex entity extraction
│   ├── graph_engine.py             # NetworkX graph analytics & Louvain clustering
│   ├── prediction_engine.py        # Machine learning inference engine
│   └── pattern_detector.py         # Anomaly, burst & pattern detection
└── static/
    ├── index.html                  # Investigator dashboard UI (8 tabs)
    ├── css/
    │   └── styles.css              # Cyber-sleek dark theme with glassmorphism
    └── js/
        └── app.js                  # Frontend state management, Chart.js & vis.js integration
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or 3.11 (Python 3.11 recommended)
- `pip` package manager

### 1. Clone the Repository
```bash
git clone https://github.com/VinamraBhatnagar/KAYA-HACKTHON.git
cd KAYA-HACKTHON
```

### 2. Set Up Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
python3 -m spacy download en_core_web_sm
```

### 4. Generate or Refresh Datasets
```bash
python3 data/generate_synthetic_data.py
```

### 5. Launch the Application

```bash
# Standard mode (Fast startup with heuristic ML fallback)
python3 app.py

# Full ML mode (Loads trained Random Forest models if available)
LOAD_ML_MODELS=true python3 app.py
```

### 6. Access Investigator Dashboard
Open your browser and navigate to:
```
http://localhost:5001
```

---

## 🤖 Machine Learning Models

The system is designed to interface with pre-trained Random Forest models trained on historical crime data:

| Model | File / Path | Classes / Target |
|---|---|---|
| **Crime Type Classifier** | `models 2/crime_type_random_forest_optimized.pkl` | 15 Crime Categories |
| **Arrest Probability Model** | `models 2/arrest_random_forest.joblib` | Binary (Arrest Made: Yes/No) |
| **Fallback Crime Model** | `models/crime_type_random_forest.joblib` | Multi-class Classifier |

> **Note on Model Files**: Due to GitHub's 100MB file limit, binary `.joblib` / `.pkl` models (~3.5 GB total) are excluded from the git repository via `.gitignore`. The application automatically operates with high-precision statistical and heuristic fallback scoring when model files are not present locally.

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dashboard` | Aggregated KPIs, risk distribution, trends, recent alerts |
| `GET` | `/api/network` | Complete network graph nodes, edges, and relationship types |
| `GET` | `/api/network/communities` | Detected criminal syndicates / modularity communities |
| `GET` | `/api/network/influencers` | Top nodes ranked by Degree, Betweenness, and PageRank |
| `GET` | `/api/network/path?source=<ID>&target=<ID>` | Shortest path and connection chain between entities |
| `GET` | `/api/entities` | List or query all indexed entities (`?q=query`) |
| `GET` | `/api/entity/<id>` | Entity dossier, associate list, criminal records, activity logs |
| `POST`| `/api/predict/crime-type` | Predict crime category from location, time, and flags |
| `POST`| `/api/predict/arrest` | Predict arrest probability for an incident |
| `GET` | `/api/patterns` | Detected anomalies (burst calls, high-value transactions, etc.) |
| `GET` | `/api/timeline` | Unified chronological incident and communication timeline |
| `POST`| `/api/analyze-text` | Real-time NLP entity extraction from raw text / FIR reports |
| `GET` | `/api/models` | Status and metadata of loaded ML models |

---

## 🛡️ Security & Privacy
This software is intended for research, hackathon demonstration, and legitimate investigative assistance. In production deployments:
- Enforce Role-Based Access Control (RBAC).
- Implement end-to-end encryption for stored CDRs and financial records.
- Comply with jurisdictional data protection regulations (e.g., GDPR, CJIS standards).

---

## 👥 Authors & Acknowledgments

- **Vinamra Bhatnagar** — Project Lead & Developer
- **Team Kaya** — KAYA Hackathon

Special thanks to the open-source community for **NetworkX**, **spaCy**, **scikit-learn**, **Chart.js**, and **vis.js**.
