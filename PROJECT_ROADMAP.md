# 🗺️ CrimeNet AI — Technical Deliverables & Future Roadmap

**Project**: CrimeNet AI — AI-Powered Criminal Network Analysis System  
**Hackathon**: KAYA Hackathon  
**Author**: Vinamra Bhatnagar (Team Kaya)

---

## 📊 Summary Matrix: What Is Done vs What Has To Be Done

| Subsystem | What Has Been Completed (Delivered) | What Has To Be Done (Future Roadmap) | Priority |
|---|---|---|---|
| **Dynamic Intel Ingestion** | **Live Ingestion Console (➕ Add Criminal / Crime)**: Dynamic registration of new suspects and FIR incidents; auto-ID generation (`SUSP_xxx`, `INC_xxxx`), auto-linking of known associates and co-incident edges directly into active in-memory graph and index. | Drag-and-drop batch CSV/Excel parser; suspect mugshot & biometric photo upload; real-time WebSocket dispatch to all connected analyst stations upon new record creation. | High |
| **Data Ingestion & Pipeline** | Synthetic data generator for 5 interconnected sources (suspects, incidents, CDRs, transactions, criminal history); in-memory multi-entity indexing and lookup engine. | Live Socrata Open Data API connector for Chicago Crime Portal; Kafka / RabbitMQ streaming consumers for real-time CDR telecom and banking transaction feeds. | High |
| **Graph Analytics** | NetworkX multi-relational graph (5 edge types: `KNOWN_ASSOCIATE`, `CO_INCIDENT`, `COMMUNICATION`, `FINANCIAL`, `MEMBER_OF`), Louvain community detection, multi-centrality influencer ranking (Degree, Betweenness, Closeness, PageRank), shortest path multi-hop finder. | Migration to Neo4j / Amazon Neptune graph database; incremental real-time graph updates without full recalculation; billion-edge enterprise scale. | High |
| **Machine Learning** | scikit-learn Random Forest model wrapper; feature engineering for spatiotemporal attributes; high-precision heuristic fallback engine for crime classification and arrest likelihood. | Graph Neural Networks (GNN) via PyTorch Geometric / Node2Vec for predicting hidden unrecorded accomplice links; Temporal Graph Networks (TGN). | Critical |
| **NLP & Text Analysis** | spaCy NER pipeline + custom regex extractors (`PERSON`, `ORGANIZATION`, `LOCATION`, `PHONE`, `VEHICLE_PLATE`); threat severity keyword scoring; entity co-occurrence relationship inference from unstructured FIRs. | Fine-tuned open-source local LLM (Llama-3 / Mistral 7B) for natural language conversational querying over crime intelligence dossiers and automatic FIR narrative generation. | Medium |
| **Pattern Detection & Alerts** | Anomaly detector flagging behavioral recidivists, financial structuring (smurfing), communication bursts, geographic hotspots, and network brokers. **Bug Fix**: Stateful non-destructive pattern filter engine preserving full pattern pool across severity toggles (Critical ↔ High ↔ Medium ↔ Low). | Unsupervised isolation forests and autoencoders for zero-day organized crime patterns; automated dynamic risk score re-weighting. | Medium |
| **Geospatial Intelligence** | Top crime location aggregations, crime hotspot concentration detection, and district/ward analytics. | Interactive Leaflet / Mapbox GIS spatial map with incident pin heatmaps, spatial radius filtering, and cell tower triangulation routes. | High |
| **Multi-Modal Intelligence** | Text-based FIR parsing, telephone record extraction, and structured transaction ledgers. | OpenAI Whisper audio pipeline for wiretap and interrogation recordings; Tesseract OCR for scanned physical FIRs and evidence documents. | Medium |
| **UI & Tactical Theme** | **Cyber-Forensics Tactical Intelligence Command Theme**: Immersive high-tech HUD styling with deep tactical obsidian canvas (`#060a14`), glowing cyber cyan (`#00f0ff`), radar emerald (`#10b981`), alert amber (`#ffb703`), hazard crimson (`#ff2e5b`), glassmorphism card panels, cyber radar grid graph canvas, and optional Light Mode toggle. 9 full tabs. | Export court-admissible PDF intelligence briefing dossiers; custom graph layout export (SVG/PNG); mobile-optimized field officer views. | High |
| **Security & Compliance** | Standalone Flask architecture with CORS and REST JSON contracts across 15 endpoints. | Role-Based Access Control (RBAC); JWT session tokens; CJIS audit trail logging for all investigator lookups; PostgreSQL database with Row-Level Security. | Critical |

---

## 📍 Detailed Technical Roadmap

### Phase 1: Real-Time Stream Ingestion & Evidence Vault (Weeks 1–4)
1. **Live Chicago Crime API Sync**:
   - Scheduled cron job querying `data.cityofchicago.org/resource/ijzp-q8t2.json`.
   - Incremental batch ingestion of newly filed police reports.
2. **Streaming Event Bus**:
   - Apache Kafka broker streaming simulated or live telecom CDR events and bank wire transactions.
   - Microservice architecture decoupling ingestion from the graph query engine.
3. **Biometric & Evidence Vault**:
   - Multi-file attachment system allowing investigators to upload suspect mugshots, fingerprint scans, and ballistic reports with SHA-256 integrity verification.

### Phase 2: Deep Learning Graph Link Prediction (Weeks 5–8)
1. **Graph Neural Networks (PyTorch Geometric)**:
   - Train **GraphSAGE** and **Node2Vec** embeddings on the knowledge graph.
   - Infer high-probability hidden edges: *"Suspect X and Suspect Y have no direct calls, but their transaction and associate topology indicates an 87% likelihood of being co-conspirators."*
2. **Temporal Graph Dynamics**:
   - Interactive timeline slider in frontend to watch a syndicate grow, mutate, and fragment over a multi-year timeline.

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
