# 🔍 CrimeNet AI — AI-Powered Criminal Network Analysis System

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-000000.svg?style=flat&logo=flask&logoColor=white)](https://palletsprojects.com/p/flask/)
[![scikit-learn](https://img.shields.io/badge/ML-scikit--learn-F7931E.svg?style=flat&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![NetworkX](https://img.shields.io/badge/Graph-NetworkX-blue.svg?style=flat)](https://networkx.org/)
[![spaCy](https://img.shields.io/badge/NLP-spaCy-09A3D5.svg?style=flat&logo=spacy&logoColor=white)](https://spacy.io/)
[![UI Theme](https://img.shields.io/badge/Theme-Cyber--Forensics%20Tactical%20HUD-00f0ff.svg?style=flat)](#)
[![Hackathon](https://img.shields.io/badge/Hackathon-KAYA-purple.svg?style=flat)](#)

> **Autonomous Multi-Source Intelligence Fusion & Graph Analytics Engine for Law Enforcement & Investigative Agencies.**

Developed for the **KAYA Hackathon** by **Team Kaya**.

---

## 📌 Problem Background

Modern criminal organizations operate as distributed, decentralized networks involving associates, shell companies, informal financial conduits (hawala/cash structuring), encrypted communications, and coordinated logistical events. 

Law enforcement agencies gather massive volumes of intelligence from fragmented sources:
- First Information Reports (FIRs) and police incident logs
- Call Detail Records (CDRs) and telecommunication traces
- Financial transactions, wire transfers, and bank records
- Physical surveillance logs and vehicle sightings
- Criminal history registries and prior conviction databases

**The Core Investigative Challenge**: Because data resides in isolated silos and unstructured formats, manual investigative linkage is slow, labor-intensive, and prone to missing multi-hop connections. **CrimeNet AI** solves this by unifying fragmented data into an interactive Knowledge Graph, applying machine learning risk models, extracting entities with NLP, and proactively surfacing hidden syndicates and crime anomalies.

---

## 📋 Project Status: What Is Done vs What Has To Be Done

A transparent, comprehensive breakdown of what has been built and delivered in this project, alongside the future technical roadmap for production readiness.

### ✅ What Is Done (Completed & Operational)

#### 1. End-to-End Data Pipeline & Synthetic Data Generator
- [x] **Synthetic Data Generator Engine** (`data/generate_synthetic_data.py`): Generates interconnected, highly realistic multi-source law enforcement datasets:
  - 80 Suspect Profiles with aliases, risk classifications, affiliations, and phone numbers (`data/suspects.json`, `data/suspects.csv`).
  - 500 Police Crime Incidents & FIR logs (`data/incidents.csv`).
  - 5,000 Call Detail Records (CDRs) with timestamps, durations, and call types (`data/cdr_records.csv`).
  - 2,000 Financial Bank Transactions & Cash Transfers (`data/financial_transactions.csv`).
  - 235 Criminal History & Prior Conviction Records (`data/criminal_history.csv`).
- [x] **Data Normalization & Unified Indexer** (`modules/data_processor.py`): Ingests all heterogeneous data sources and builds an in-memory unified entity index linking suspects, phones, accounts, vehicles, and organizations.

#### 2. Graph Intelligence & Social Network Analysis (SNA)
- [x] **Multi-Relational Knowledge Graph** (`modules/graph_engine.py`): Built with **NetworkX**, modeling 5 distinct relationship types:
  - `KNOWN_ASSOCIATE` (prior intelligence links)
  - `CO_INCIDENT` (shared crime events/FIRs)
  - `COMMUNICATION` (frequency & duration-weighted CDR calls)
  - `FINANCIAL` (transaction volume & amount-weighted money flows)
  - `MEMBER_OF` (affiliation with cartels or syndicates)
- [x] **Community Detection**: Implements the **Louvain Modularity Algorithm** to automatically partition the graph into hidden criminal syndicates and operational sub-cells.
- [x] **Multi-Metric Centrality Scoring**: Evaluates suspects across Degree, Betweenness, Closeness Centrality, and PageRank to identify key kingpins and communication brokers.
- [x] **Shortest Path Analysis**: Calculates multi-hop connection chains and degrees of separation between any two selected entities.

#### 3. Machine Learning Crime & Arrest Prediction Engine
- [x] **ML Inference Engine** (`modules/prediction_engine.py`):
  - Pre-trained **Random Forest Classifiers** trained on historical Chicago Crime data (predicting 15 crime categories and arrest likelihood).
  - Feature engineering pipeline matching spatiotemporal features (location description, hour, day, month, domestic flags, district/ward).
  - Robust heuristic fallback engine providing instant predictions even when multi-gigabyte model weights are not loaded locally.

#### 4. Natural Language Processing (NLP) Entity & FIR Parser
- [x] **NLP Extraction Pipeline** (`modules/nlp_engine.py`):
  - Powered by **spaCy** Named Entity Recognition (`en_core_web_sm`) combined with custom regex pattern matchers.
  - Extracts `PERSON`, `ORGANIZATION`, `LOCATION`, `PHONE`, and `VEHICLE_PLATE` from unstructured FIR narratives.
  - Threat severity keyword scoring (firearms, narcotics, smuggling, extortion).
  - Co-occurrence relation extraction between co-mentioned suspects and locations.

#### 5. Pattern & Anomaly Detection System
- [x] **Multi-Domain Anomaly Detector** (`modules/pattern_detector.py`):
  - **Behavioral Patterns**: Identifies high-frequency repeat offenders and escalation of charges.
  - **Financial Anomalies**: Detects structuring (smurfing below reporting thresholds) and rapid large-sum transfers.
  - **Communication Bursts**: Detects sudden spikes in call volume preceding major incidents.
  - **Geographic Clusters**: Flags high-density crime location hotspots.
  - **Network Brokers**: Highlights bridge nodes connecting otherwise disjoint criminal factions.

#### 6. Investigator Command Center UI
- [x] **Cyber-Forensics Tactical Intelligence Command Theme (Default)** with **Light Mode Toggle**:
  - Purpose-built tactical HUD aesthetics reflecting modern cyber crime labs and national intelligence operations.
  - Deep obsidian canvas (`#060a14`), glowing cyber cyan (`#00f0ff`), radar emerald (`#10b981`), alert amber (`#ffb703`), and hazard crimson (`#ff2e5b`).
  - Frosted glassmorphism card panels (`rgba(11, 18, 35, 0.8)`), glowing border accents, and high-tech cyber radar grid backdrop on the network canvas.
  - Interactive Theme Toggle in top bar persisting user preference in `localStorage`.
- [x] **9 Specialized Intelligence Tabs**:
  1. **Dashboard**: Executive KPIs, monthly crime trend line, risk level distribution, and crime type doughnut chart.
  2. **Network Graph**: Interactive force-directed canvas powered by **vis.js** with zoom, drag, physics toggle, community coloring, and node detail modals.
  3. **Entity Explorer**: Searchable and filterable suspect dossier registry with quick-action profile inspection.
  4. **Communities**: Clustered view of detected syndicates with membership lists and threat ratings.
  5. **Patterns & Alerts**: Real-time triage feed of 200+ detected suspicious activities with non-destructive severity filters (All, Critical, High, Medium, Low).
  6. **Key Influencers**: Leaderboard ranking prime targets by composite network centrality.
  7. **Add Criminal / Crime (Live Ingest Console)**: Form to register new suspects and log FIR incidents with real-time graph node injection and accomplice linking.
  8. **Prediction Console**: Form to test hypothetical crime scenarios against the ML models.
  9. **NLP Analyzer**: Live text area to paste FIR reports and visualize extracted entities instantly.

#### 7. REST API & Architecture
- [x] **15 REST API Endpoints** in Flask (`app.py`) with structured JSON contracts (including live suspect & incident ingestion).
- [x] Complete test suite verification across all endpoints and data pipelines.
- [x] GitHub repository synchronization and `.gitignore` setup preventing large model binary bloat.

---

### ⏳ What Has To Be Done (Future Roadmap & Pending Enhancements)

While CrimeNet AI provides a functional prototype and intelligence platform, the following initiatives represent the roadmap for enterprise production deployment:

#### 1. Live Data Ingestion & Streaming Pipelines
- [ ] **Direct Socrata / Police Portal API Connector**: Connect directly to live city open-data APIs (e.g. Chicago Data Portal) for scheduled real-time incident polling.
- [ ] **Kafka / RabbitMQ Event Streaming**: Ingest live CDR telecom records and core banking transaction streams via message queues instead of batch CSV processing.
- [ ] **Incremental Graph Updater**: Enable streaming real-time graph updates so new phone calls and transactions instantly update centrality metrics without full graph rebuilds.

#### 2. Advanced Graph Neural Networks (GNN) & Deep Learning
- [ ] **GNN Link Prediction (PyTorch Geometric / Node2Vec / GraphSAGE)**: Train graph neural networks to predict hidden, unrecorded associations between suspects (e.g., predicting that Suspect A communicates with Suspect B through an unmonitored burner phone).
- [ ] **Temporal Graph Networks (TGN)**: Model how criminal networks evolve over time, showing syndicate expansion, fragmentation, and cell formation across months and years.
- [ ] **Fine-Tuned Legal/Police LLM (Llama-3 / Mistral LoRA)**: Deploy a specialized local LLM to draft automated intelligence summaries, cross-reference FIR inconsistencies, and answer natural language queries (e.g. *"Show me all associates of Vijay Patel involved in narcotics within 5km of Sector 18"*).

#### 3. Geospatial GIS Mapping & Route Trajectory
- [ ] **Interactive GIS Map (Leaflet / Mapbox GL)**:
  - Render incident locations and suspect addresses on a live street-level map.
  - Density heatmaps for crime hotspots and temporal time-slider animations.
  - Cell tower triangulation visualization showing suspect movement vectors based on CDR tower IDs.

#### 4. Multi-Modal Intelligence Ingestion
- [ ] **Automated Wiretap Audio Transcription (OpenAI Whisper)**: Ingest intercepted audio calls, transcribe them into text, translate regional dialects, and pipe transcripts directly through the NLP entity extractor.
- [ ] **Computer Vision & OCR Pipeline**: Optical Character Recognition for scanned paper FIRs, handwritten police diary logs, and facial recognition matching against suspect photo registries.

#### 5. Production Security, Database Migration & Compliance
- [ ] **Persistent Graph Database Migration**: Migrate the graph store from in-memory NetworkX to **Neo4j** or **Amazon Neptune** with Cypher query optimization for billion-edge scalability.
- [ ] **Relational Store Migration**: Replace local CSV files with an encrypted **PostgreSQL** database with row-level security (RLS).
- [ ] **Role-Based Access Control (RBAC)**: Implement authentication (OAuth2 / JWT) with role tiers (Investigating Officer, Senior Analyst, Evidence Auditor).
- [ ] **CJIS & Data Privacy Audit Trails**: Tamper-evident logging of all searches, graph traversals, and dossier exports for court admissibility and legal compliance.
- [ ] **One-Click Intelligence Briefing PDF Export**: Generate court-ready PDF briefing packets containing suspect dossiers, network subgraphs, call timelines, and anomaly evidence.

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    Heterogeneous Intelligence Sources                      │
│   [Police FIRs]    [CDR Telephony]    [Bank Records]    [Criminal History] │
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                    Ingestion, Normalization & NLP Core                     │
│  ┌───────────────────────────────┐   ┌──────────────────────────────────┐  │
│  │   Data Processor & Indexer    │   │   spaCy NER & Regex Pipeline     │  │
│  │   (modules/data_processor.py) │   │   (modules/nlp_engine.py)        │  │
│  └───────────────────────────────┘   └──────────────────────────────────┘  │
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                      Intelligence & Analytics Layer                        │
│  ┌───────────────────────────────┐   ┌──────────────────────────────────┐  │
│  │   NetworkX Graph Engine       │   │   Machine Learning Predictor     │  │
│  │   Louvain Modularity + SNA    │   │   Random Forest Classifiers      │  │
│  │   (modules/graph_engine.py)   │   │   (modules/prediction_engine.py) │  │
│  └───────────────────────────────┘   └──────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │   Multi-Domain Pattern & Anomaly Detector (modules/pattern_detector) │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │ REST API (13 Endpoints)
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│            Investigator Command Center UI (Vibrant Bright / Dark)          │
│    Dashboard │ Network Graph │ Entities │ Communities │ Alerts │ NLP Tool  │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10 or 3.11 (Python 3.11 recommended)
- `pip` package manager
- Web browser (Chrome, Firefox, Safari, Edge)

### 1. Clone the Repository
```bash
git clone https://github.com/VinamraBhatnagar/KAYA-HACKTHON.git
cd KAYA-HACKTHON
```

### 2. Set Up Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate
```

### 3. Install Required Dependencies
```bash
pip install -r requirements.txt
python3 -m spacy download en_core_web_sm
```

### 4. Generate or Regenerate Datasets
```bash
python3 data/generate_synthetic_data.py
```

### 5. Launch the Server

```bash
# Standard mode (Fast startup with heuristic ML fallback)
python3 app.py

# Full ML mode (Loads pre-trained Random Forest models if available)
LOAD_ML_MODELS=true python3 app.py
```

### 6. Access the Dashboard
Open your browser and navigate to:
```
http://localhost:5001
```

> **Theme Customization**: CrimeNet AI opens with the **Cyber-Forensics Tactical Command Theme** by default. Click the **☀️ Light Mode** button in the top-right header anytime to switch between Cyber and Light modes!

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dashboard` | High-level KPIs, crime distributions, and monthly trends |
| `GET` | `/api/network` | Full knowledge graph with nodes, edges, weights, and relations |
| `GET` | `/api/network/communities` | Detected criminal syndicates partitioned by Louvain clustering |
| `GET` | `/api/network/influencers` | Top 20 network influencers ranked by composite centrality |
| `GET` | `/api/network/path?source=<ID>&target=<ID>` | Shortest connection path between any two targets |
| `GET` | `/api/entities` | Searchable registry of suspects, orgs, and locations (`?q=term`) |
| `GET` | `/api/entity/<id>` | Full intelligence dossier, associates, records, and history |
| `POST`| `/api/suspects/add` | Dynamically register a new suspect & inject into the graph |
| `POST`| `/api/incidents/add` | Log a new crime incident/FIR & link co-suspects in real-time |
| `POST`| `/api/predict/crime-type` | Multi-class crime category prediction from spatiotemporal inputs |
| `POST`| `/api/predict/arrest` | Binary arrest likelihood prediction |
| `GET` | `/api/patterns` | Feed of detected behavioral, financial, and geographic anomalies |
| `GET` | `/api/timeline` | Unified chronological incident and communication timeline |
| `POST`| `/api/analyze-text` | Real-time NLP entity extraction from raw FIR or informant text |
| `GET` | `/api/models` | Loaded status and metadata of machine learning models |

---

## 📁 Repository Directory Structure

```
KAYA-HACKTHON/
├── app.py                          # Flask application server & REST routing
├── requirements.txt                # Pinned dependencies (scikit-learn==1.6.1, spaCy, NetworkX)
├── README.md                       # Complete project documentation & status roadmap
├── .gitignore                      # Excludes large binaries (>3.5GB) and local caches
├── data/
│   ├── generate_synthetic_data.py  # Multi-source realistic synthetic intelligence generator
│   ├── suspects.json               # Seed suspects with aliases, risk ratings, and affiliations
│   ├── suspects.csv                # Tabular suspect profile registry
│   ├── incidents.csv               # Crime incidents & FIR reports
│   ├── cdr_records.csv             # Telephony call & SMS detail records
│   ├── financial_transactions.csv  # Bank transfers & cash transactions
│   └── criminal_history.csv        # Historical conviction and arrest records
├── modules/
│   ├── __init__.py                 # Python package init
│   ├── data_processor.py           # Ingestion, normalization & unified entity indexing
│   ├── nlp_engine.py               # spaCy NER + regex entity & relation extraction
│   ├── graph_engine.py             # NetworkX graph analytics & Louvain community detection
│   ├── prediction_engine.py        # Random Forest inference & heuristic risk scoring
│   └── pattern_detector.py         # Temporal, financial, geographic & network anomaly detection
└── static/
    ├── index.html                  # 9-tab investigator command dashboard & ingest console
    ├── css/
    │   └── styles.css              # Cyber-Forensics Tactical theme (default) + Light HUD
    └── js/
        └── app.js                  # Application state, Chart.js, vis.js, dynamic ingest & theme switcher
```

---

## 🛡️ Responsible AI & Ethical Disclosure
This software is intended for research, hackathon evaluation, and lawful intelligence support. In real-world police deployments, algorithmic predictions must serve strictly as investigative aids rather than definitive proof of criminality. Rigorous human oversight, bias auditing, and constitutional protections must guide all operational implementations.

---

## 👥 Contributors & Acknowledgments

- **Vinamra Bhatnagar** — Project Lead & Full-Stack / ML Developer
- **Team Kaya** — KAYA Hackathon

Special thanks to the developers of **NetworkX**, **spaCy**, **scikit-learn**, **Chart.js**, and **vis.js** for making open-source graph and data science tools accessible.
