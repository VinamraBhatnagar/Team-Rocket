# 🗺️ CrimeNet AI — Technical Deliverables & Future Roadmap

**Project**: CrimeNet AI — AI-Powered Criminal Network Analysis System  
**Hackathon**: KAYA Hackathon  
**Author**: Vinamra Bhatnagar (Team Kaya)

---

## 📊 Summary Matrix: What Is Done vs What Has To Be Done

| Subsystem | What Has Been Completed (Delivered) | What Has To Be Done (Future Roadmap) | Priority |
|---|---|---|---|
| **Data Ingestion** | Synthetic data generator for 5 sources (suspects, incidents, CDRs, transactions, criminal history); in-memory indexing pipeline. | Live Socrata Open Data API connector for Chicago Crime Portal; Kafka / RabbitMQ streaming consumers for live CDR & banking feeds. | High |
| **Graph Analytics** | NetworkX multi-relational graph (5 edge types), Louvain community detection, multi-centrality influencer ranking (Degree, Betweenness, Closeness, PageRank), shortest path finder. | Migration to Neo4j / Amazon Neptune graph database; incremental real-time graph updates without full recalculation; billion-edge scale. | High |
| **Machine Learning** | scikit-learn Random Forest model wrapper; feature engineering for spatiotemporal data; high-precision heuristic fallback engine. | Graph Neural Networks (GNN) via PyTorch Geometric / Node2Vec for predicting hidden unrecorded accomplice links; Temporal Graph Networks (TGN). | Critical |
| **NLP & Text Analysis** | spaCy NER pipeline + custom regex extractors (Person, Org, Location, Phone, Plates); severity keyword scorer; entity co-occurrence relationship inference. | Fine-tuned open-source local LLM (Llama-3 / Mistral 7B) for natural language querying over crime intelligence dossiers and automatic FIR narrative generation. | Medium |
| **Pattern Detection** | Anomaly detector flagging behavioral recidivists, financial structuring (smurfing), communication bursts, geographic hotspots, and network brokers. | Unsupervised isolation forests and autoencoders for zero-day organized crime patterns; automated risk scoring updates. | Medium |
| **Geospatial Intelligence** | Top crime location aggregations and district/ward analytics. | Interactive Leaflet / Mapbox GIS spatial map with incident pin heatmaps, spatial radius filtering, and cell tower triangulation routes. | High |
| **Multi-Modal Intelligence** | Text-based FIR parsing and tabular structured records. | OpenAI Whisper audio pipeline for wiretap and interrogation recordings; Tesseract OCR for scanned physical FIRs and evidence documents. | Medium |
| **UI & Experience** | 8-tab investigative dashboard; Chart.js & vis.js integration; **Vibrant Bright Color Theme (Default)** with Dark Theme toggle. | Export court-admissible PDF intelligence briefing dossiers; custom graph layout filtering; mobile-optimized field officer views. | High |
| **Security & Compliance** | Standalone Flask architecture with CORS and REST JSON contracts. | Role-Based Access Control (RBAC); JWT session tokens; CJIS audit trail logging for all investigator lookups; PostgreSQL database with Row-Level Security. | Critical |

---

## 📍 Detailed Technical Roadmap

### Phase 1: Real-Time Stream Ingestion (Weeks 1–4)
1. **Live Chicago Crime API Sync**:
   - Scheduled cron job querying `data.cityofchicago.org/resource/ijzp-q8t2.json`.
   - Incremental batch ingestion of newly filed police reports.
2. **Streaming Event Bus**:
   - Apache Kafka broker streaming simulated or live telecom CDR events and bank wire transactions.
   - Microservice architecture decoupling ingestion from the graph query engine.

### Phase 2: Deep Learning Graph Link Prediction (Weeks 5–8)
1. **Graph Neural Networks (PyTorch Geometric)**:
   - Train **GraphSAGE** and **Node2Vec** embeddings on the knowledge graph.
   - Infer high-probability hidden edges: *"Suspect X and Suspect Y have no direct calls, but their transaction and associate topology indicates an 87% likelihood of being co-conspirators."*
2. **Temporal Graph Dynamics**:
   - Slider UI in frontend to watch a syndicate grow, mutate, and fragment over a 12-month timeline.

### Phase 3: Geospatial GIS Intelligence (Weeks 9–12)
1. **Interactive Mapbox / Leaflet Layer**:
   - GeoJSON mapping of incident coordinates (Latitude / Longitude).
   - Time-series heatmaps of robbery, narcotics, and weapon violations.
   - Cell tower triangulation polygons showing suspect whereabouts during crime windows.

### Phase 4: Multi-Modal Audio & Document Processing (Weeks 13–16)
1. **Wiretap Speech-to-Text**:
   - Ingest intercepted audio calls (.mp3, .wav), transcribe with OpenAI Whisper.
   - Automatically pass generated transcripts into the NLP entity extraction pipeline.
2. **OCR for Scanned FIRs**:
   - Ingest PDF or JPEG scanned police reports.
   - Extract text with Tesseract / Google Document AI and map to suspects automatically.

### Phase 5: Enterprise Hardening & Law Enforcement Compliance (Weeks 17–20)
1. **Database Persistence Migration**:
   - Store entities and tabular logs in **PostgreSQL**.
   - Store graph topology in **Neo4j** using Cypher queries for sub-second multi-hop traversals.
2. **Access Control & Auditing**:
   - Role-Based Access Control (Investigator, Supervisor, Admin).
   - Audit logs recording every query, node inspection, and export for legal and chain-of-custody compliance.
3. **Automated Intelligence Dossier Export**:
   - Generate polished, court-ready PDF briefing binders containing suspect profiles, associate subgraphs, call records, and anomaly chronologies.
