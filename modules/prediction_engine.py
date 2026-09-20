"""
Prediction Engine
Wrapper for the trained ML models (crime type prediction & arrest prediction).
Loads and caches the scikit-learn models and handles feature preprocessing.
"""

import os
import math
import numpy as np

try:
    import joblib
    _JOBLIB_AVAILABLE = True
except ImportError:
    _JOBLIB_AVAILABLE = False

try:
    import pickle
    _PICKLE_AVAILABLE = True
except ImportError:
    _PICKLE_AVAILABLE = False


class PredictionEngine:
    """Wrapper for trained ML models."""

    def __init__(self, models_dir="models", models2_dir="models 2"):
        self.models_dir = models_dir
        self.models2_dir = models2_dir
        self.crime_type_model = None
        self.arrest_model = None
        self.optimized_model = None
        self._loaded = False

    def load_models(self):
        """Load all available models."""
        print("🤖 Loading ML models...")

        # Load optimized crime type model (preferred — smaller, better features)
        opt_path = os.path.join(self.models2_dir, "crime_type_random_forest_optimized.pkl")
        if os.path.exists(opt_path):
            try:
                with open(opt_path, 'rb') as f:
                    self.optimized_model = pickle.load(f)
                print(f"  ✅ Optimized crime type model loaded ({os.path.getsize(opt_path) / 1e6:.0f} MB)")
            except Exception as e:
                print(f"  ⚠️  Could not load optimized model: {e}")

        # Load arrest prediction model
        arrest_path = os.path.join(self.models2_dir, "arrest_random_forest.joblib")
        if os.path.exists(arrest_path) and _JOBLIB_AVAILABLE:
            try:
                self.arrest_model = joblib.load(arrest_path)
                print(f"  ✅ Arrest prediction model loaded ({os.path.getsize(arrest_path) / 1e6:.0f} MB)")
            except Exception as e:
                print(f"  ⚠️  Could not load arrest model: {e}")

        # Load original crime type model as fallback
        crime_path = os.path.join(self.models_dir, "crime_type_random_forest.joblib")
        if os.path.exists(crime_path) and _JOBLIB_AVAILABLE and self.optimized_model is None:
            try:
                self.crime_type_model = joblib.load(crime_path)
                print(f"  ✅ Crime type model loaded ({os.path.getsize(crime_path) / 1e6:.0f} MB)")
            except Exception as e:
                print(f"  ⚠️  Could not load crime type model: {e}")

        self._loaded = True
        available = sum(1 for m in [self.optimized_model, self.crime_type_model, self.arrest_model] if m is not None)
        print(f"  📊 {available} models available")

    def predict_crime_type(self, hour, day_of_week, month, beat, district,
                           community_area, location_description):
        """
        Predict crime type given spatiotemporal features.
        Uses the optimized model if available, else falls back to original.
        """
        model = self.optimized_model or self.crime_type_model
        if model is None:
            return self._mock_crime_prediction(hour, location_description)

        try:
            if self.optimized_model:
                # Optimized model expects cyclical encoding
                import pandas as pd
                features = pd.DataFrame([{
                    "Hour_sin": math.sin(2 * math.pi * hour / 24),
                    "Hour_cos": math.cos(2 * math.pi * hour / 24),
                    "Month_sin": math.sin(2 * math.pi * month / 12),
                    "Month_cos": math.cos(2 * math.pi * month / 12),
                    "DayOfWeekNum": day_of_week,
                    "Beat": beat,
                    "District": district,
                    "Community Area": community_area,
                    "Location Description": location_description
                }])
            else:
                # Original model expects raw features
                import pandas as pd
                features = pd.DataFrame([{
                    "Hour": hour,
                    "DayOfWeekNum": day_of_week,
                    "Month": month,
                    "Beat": beat,
                    "District": district,
                    "Community Area": community_area,
                    "Location Description": location_description
                }])

            prediction = model.predict(features)[0]
            probabilities = model.predict_proba(features)[0]
            classes = model.classes_

            # Get top 5 predictions with probabilities
            prob_dict = {str(c): round(float(p) * 100, 2) for c, p in zip(classes, probabilities)}
            top5 = sorted(prob_dict.items(), key=lambda x: x[1], reverse=True)[:5]

            return {
                "prediction": str(prediction),
                "confidence": round(float(max(probabilities)) * 100, 2),
                "top_predictions": [{"crime_type": k, "probability": v} for k, v in top5],
                "model_used": "optimized" if self.optimized_model else "original",
                "features_used": list(features.columns),
            }
        except Exception as e:
            return {"error": str(e), "prediction": None}

    def predict_arrest(self, hour, day_of_week, month, beat, district,
                       community_area, primary_type, location_description):
        """Predict arrest probability given incident features."""
        if self.arrest_model is None:
            return self._mock_arrest_prediction(primary_type)

        try:
            import pandas as pd
            features = pd.DataFrame([{
                "Hour": hour,
                "DayOfWeekNum": day_of_week,
                "Month": month,
                "Beat": beat,
                "District": district,
                "Community Area": community_area,
                "Primary Type": primary_type,
                "Location Description": location_description
            }])

            prediction = self.arrest_model.predict(features)[0]
            probabilities = self.arrest_model.predict_proba(features)[0]

            return {
                "arrest_likely": bool(prediction),
                "arrest_probability": round(float(probabilities[1]) * 100, 2),
                "no_arrest_probability": round(float(probabilities[0]) * 100, 2),
                "model_used": "arrest_random_forest",
            }
        except Exception as e:
            return {"error": str(e), "arrest_likely": None}

    def _mock_crime_prediction(self, hour, location_description):
        """Fallback when models aren't loaded — uses heuristic rules."""
        # Simple heuristic based on time and location
        if 0 <= hour <= 5:
            prediction = "BURGLARY" if "RESIDENCE" in location_description.upper() else "ROBBERY"
        elif 6 <= hour <= 11:
            prediction = "THEFT"
        elif 12 <= hour <= 17:
            prediction = "DECEPTIVE PRACTICE"
        elif 18 <= hour <= 21:
            prediction = "ASSAULT"
        else:
            prediction = "BATTERY"

        return {
            "prediction": prediction,
            "confidence": 45.0,
            "top_predictions": [
                {"crime_type": prediction, "probability": 45.0},
                {"crime_type": "THEFT", "probability": 20.0},
                {"crime_type": "BATTERY", "probability": 15.0},
                {"crime_type": "ASSAULT", "probability": 10.0},
                {"crime_type": "OTHER OFFENSE", "probability": 10.0},
            ],
            "model_used": "heuristic_fallback",
            "features_used": ["Hour", "Location Description"],
        }

    def _mock_arrest_prediction(self, primary_type):
        """Fallback for arrest prediction."""
        high_arrest_crimes = ["NARCOTICS", "WEAPONS VIOLATION", "CRIMINAL TRESPASS"]
        prob = 65.0 if primary_type in high_arrest_crimes else 30.0
        return {
            "arrest_likely": prob > 50,
            "arrest_probability": prob,
            "no_arrest_probability": 100 - prob,
            "model_used": "heuristic_fallback",
        }

    def get_model_info(self):
        """Return information about loaded models."""
        models = []
        if self.optimized_model:
            models.append({
                "name": "Crime Type Classifier (Optimized)",
                "file": "crime_type_random_forest_optimized.pkl",
                "type": "RandomForestClassifier",
                "features": list(self.optimized_model.feature_names_in_) if hasattr(self.optimized_model, 'feature_names_in_') else [],
                "classes": list(self.optimized_model.named_steps['model'].classes_) if hasattr(self.optimized_model, 'named_steps') else [],
                "n_estimators": self.optimized_model.named_steps['model'].n_estimators if hasattr(self.optimized_model, 'named_steps') else 0,
                "status": "loaded"
            })
        if self.crime_type_model:
            models.append({
                "name": "Crime Type Classifier (Original)",
                "file": "crime_type_random_forest.joblib",
                "type": "RandomForestClassifier",
                "status": "loaded"
            })
        if self.arrest_model:
            models.append({
                "name": "Arrest Predictor",
                "file": "arrest_random_forest.joblib",
                "type": "RandomForestClassifier",
                "features": list(self.arrest_model.feature_names_in_) if hasattr(self.arrest_model, 'feature_names_in_') else [],
                "status": "loaded"
            })
        if not models:
            models.append({"name": "Heuristic Fallback", "status": "active",
                           "note": "ML models not loaded, using rule-based predictions"})
        return models
