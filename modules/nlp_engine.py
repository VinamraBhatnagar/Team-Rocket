"""
NLP Entity Extraction Engine
Extracts named entities from unstructured text (FIR reports, intelligence memos).
Uses spaCy for NER and custom regex patterns for domain-specific entities.
"""

import re
from collections import defaultdict

try:
    import spacy
    _SPACY_AVAILABLE = True
except ImportError:
    _SPACY_AVAILABLE = False


class NLPEngine:
    """NLP-based entity extraction from unstructured criminal reports."""

    def __init__(self):
        self.nlp = None
        self._init_spacy()
        self._compile_patterns()

    def _init_spacy(self):
        """Initialize spaCy model."""
        if not _SPACY_AVAILABLE:
            print("  ⚠️  spaCy not available, using regex-only extraction")
            return
        try:
            self.nlp = spacy.load("en_core_web_sm")
            print("  ✅ spaCy model loaded (en_core_web_sm)")
        except OSError:
            print("  ⚠️  spaCy model not found, downloading...")
            import subprocess
            subprocess.run(["python3", "-m", "spacy", "download", "en_core_web_sm"],
                           capture_output=True)
            try:
                self.nlp = spacy.load("en_core_web_sm")
                print("  ✅ spaCy model downloaded and loaded")
            except Exception:
                print("  ⚠️  Could not load spaCy model, using regex-only extraction")

    def _compile_patterns(self):
        """Compile regex patterns for domain-specific entity extraction."""
        self.patterns = {
            "PHONE": re.compile(r'\+?\d{1,3}[-.\s]?\d{4,5}[-.\s]?\d{4,5}'),
            "VEHICLE_PLATE": re.compile(
                r'[A-Z]{2}[-\s]?\d{1,2}[-\s]?[A-Z]{1,3}[-\s]?\d{3,4}'
            ),
            "CASE_ID": re.compile(r'FIR[-\s]?\d{4}[-\s]?\d{4,6}'),
            "MONEY_INR": re.compile(r'₹[\d,]+(?:\.\d{2})?|Rs\.?\s*[\d,]+'),
            "EMAIL": re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
            "AADHAAR": re.compile(r'\d{4}[-\s]?\d{4}[-\s]?\d{4}'),
            "IMEI": re.compile(r'\b\d{15}\b'),
            "DATE_PATTERN": re.compile(
                r'\d{4}[-/]\d{2}[-/]\d{2}(?:\s+\d{2}:\d{2}(?::\d{2})?)?'
            ),
            "CELL_TOWER": re.compile(r'TWR[-\s]?\d{3,5}'),
            "ACCOUNT": re.compile(r'ACCT[-\s]?\d{4,8}'),
        }

    def extract_entities(self, text):
        """
        Extract all entities from text using both spaCy NER and custom patterns.

        Returns:
            dict with entity types as keys and lists of extracted values.
        """
        entities = defaultdict(list)

        # spaCy NER
        if self.nlp and text:
            doc = self.nlp(text[:100000])  # Limit text size
            for ent in doc.ents:
                label = ent.label_
                value = ent.text.strip()
                if not value:
                    continue
                if label == "PERSON":
                    entities["PERSON"].append(value)
                elif label == "ORG":
                    entities["ORGANIZATION"].append(value)
                elif label in ("GPE", "LOC", "FAC"):
                    entities["LOCATION"].append(value)
                elif label == "DATE":
                    entities["DATE"].append(value)
                elif label == "MONEY":
                    entities["MONEY"].append(value)
                elif label == "NORP":
                    entities["GROUP"].append(value)
                elif label == "EVENT":
                    entities["EVENT"].append(value)

        # Custom regex patterns
        if text:
            for ent_type, pattern in self.patterns.items():
                matches = pattern.findall(text)
                for m in matches:
                    if m.strip() and m.strip() not in entities[ent_type]:
                        entities[ent_type].append(m.strip())

        # Deduplicate
        for key in entities:
            entities[key] = list(dict.fromkeys(entities[key]))

        return dict(entities)

    def extract_entities_batch(self, texts):
        """Extract entities from multiple texts and aggregate."""
        aggregated = defaultdict(list)
        for text in texts:
            if not text:
                continue
            result = self.extract_entities(str(text))
            for ent_type, values in result.items():
                aggregated[ent_type].extend(values)

        # Deduplicate and count
        counted = {}
        for ent_type, values in aggregated.items():
            freq = defaultdict(int)
            for v in values:
                freq[v] += 1
            counted[ent_type] = sorted(
                [{"value": k, "count": v} for k, v in freq.items()],
                key=lambda x: x["count"], reverse=True
            )

        return counted

    def analyze_text(self, text):
        """
        Comprehensive text analysis:
        - Entity extraction
        - Key phrase extraction
        - Threat level estimation
        """
        entities = self.extract_entities(text)

        # Simple keyword-based threat assessment
        threat_keywords = {
            "CRITICAL": ["murder", "terrorism", "bomb", "explosive", "assassination",
                         "mass", "hostage", "weapon of mass", "biological", "chemical"],
            "HIGH": ["weapon", "gun", "firearm", "kidnapping", "extortion", "armed",
                     "trafficking", "smuggling", "heroin", "cocaine", "laundering"],
            "MEDIUM": ["assault", "robbery", "burglary", "fraud", "forgery",
                       "narcotics", "drugs", "stolen", "counterfeit", "illegal"],
            "LOW": ["theft", "trespass", "vandalism", "disturbance", "minor",
                    "complaint", "suspicious", "investigation"]
        }

        text_lower = text.lower()
        threat_level = "LOW"
        threat_indicators = []

        for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            for kw in threat_keywords[level]:
                if kw in text_lower:
                    threat_level = level
                    threat_indicators.append(kw)
            if threat_indicators:
                break

        # Extract key sentences (sentences with most entities)
        sentences = text.split('.')
        sentence_scores = []
        for sent in sentences:
            if len(sent.strip()) < 10:
                continue
            sent_entities = self.extract_entities(sent)
            score = sum(len(v) for v in sent_entities.values())
            sentence_scores.append((sent.strip(), score))

        key_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)[:5]

        return {
            "entities": entities,
            "entity_counts": {k: len(v) for k, v in entities.items()},
            "threat_level": threat_level,
            "threat_indicators": threat_indicators,
            "key_sentences": [s[0] for s in key_sentences],
            "text_length": len(text),
            "word_count": len(text.split()),
        }

    def extract_relationships_from_text(self, text):
        """
        Extract potential relationships between entities from text.
        Returns pairs of entities that appear in close proximity.
        """
        entities = self.extract_entities(text)
        relationships = []

        persons = entities.get("PERSON", [])
        orgs = entities.get("ORGANIZATION", [])
        locations = entities.get("LOCATION", [])
        phones = entities.get("PHONE", [])

        # Person-Person relationships
        for i, p1 in enumerate(persons):
            for p2 in persons[i+1:]:
                relationships.append({
                    "source": p1, "source_type": "PERSON",
                    "target": p2, "target_type": "PERSON",
                    "relation": "CO_MENTIONED"
                })

        # Person-Organization relationships
        for p in persons:
            for o in orgs:
                relationships.append({
                    "source": p, "source_type": "PERSON",
                    "target": o, "target_type": "ORGANIZATION",
                    "relation": "ASSOCIATED_WITH"
                })

        # Person-Location relationships
        for p in persons:
            for loc in locations:
                relationships.append({
                    "source": p, "source_type": "PERSON",
                    "target": loc, "target_type": "LOCATION",
                    "relation": "SEEN_AT"
                })

        # Person-Phone relationships
        for p in persons:
            for ph in phones:
                relationships.append({
                    "source": p, "source_type": "PERSON",
                    "target": ph, "target_type": "PHONE",
                    "relation": "USES_PHONE"
                })

        return relationships
