import xgboost as xgb
import shap
import numpy as np
import pickle
from typing import Dict, List
from pathlib import Path
from ..config import settings

class MLLeadScorer:
    """XGBoost lead scoring with SHAP explanations"""
    
    def __init__(self, model_path: str = "models/lead_scorer_v1.json"):
        self.model_path = Path(model_path)
        self.model = None
        self.feature_names = [
            "keyword_match_score",
            "company_size_log",
            "industry_relevance",
            "contact_completeness",
            "email_available",
            "linkedin_available",
            "has_https",
            "description_length_log",
            "has_funding_mention",
            "tech_stack_count",
            "pain_point_match"
        ]
        self.scaler = None
        
        if self.model_path.exists():
            self.load_model()
    
    def load_model(self):
        """Load trained XGBoost model"""
        try:
            self.model = xgb.Booster()
            self.model.load_model(str(self.model_path))
            
            config_path = self.model_path.parent / "scaler.pkl"
            if config_path.exists():
                with open(config_path, "rb") as f:
                    self.scaler = pickle.load(f)
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None
    
    def extract_features(self, lead: Dict, product_analysis: Dict) -> Dict[str, float]:
        """
        Extract numerical features for ML model
        """
        
        features = {}
        
        # Keyword matching
        product_keywords = set(product_analysis.get("keywords", []))
        company_text = (lead.get("description", "") + " " + 
                       lead.get("company_name", "")).lower()
        
        matching_keywords = sum(1 for kw in product_keywords 
                               if kw.lower() in company_text)
        features["keyword_match_score"] = matching_keywords / max(len(product_keywords), 1)
        
        # Company size (log scale)
        features["company_size_log"] = np.log1p(lead.get("company_size", 0))
        
        # Industry relevance
        target_industries = set(product_analysis.get("target_industries", []))
        lead_industry = lead.get("industry", "").lower()
        features["industry_relevance"] = 1.0 if any(
            ind.lower() in lead_industry for ind in target_industries
        ) else 0.0
        
        # Contact completeness
        contact_fields = ["email", "decision_maker_name", 
                         "decision_maker_title", "linkedin_url"]
        filled = sum(1 for f in contact_fields if lead.get(f))
        features["contact_completeness"] = filled / len(contact_fields)
        
        # Binary features
        features["email_available"] = 1.0 if lead.get("email") else 0.0
        features["linkedin_available"] = 1.0 if lead.get("linkedin_url") else 0.0
        
        # Website quality
        website = lead.get("website", "")
        features["has_https"] = 1.0 if website.startswith("https") else 0.0
        
        # Description quality
        features["description_length_log"] = np.log1p(
            len(lead.get("description", ""))
        )
        
        # Funding indicators
        funding_kw = ["series a", "series b", "funded", "seed round"]
        features["has_funding_mention"] = 1.0 if any(
            kw in company_text for kw in funding_kw
        ) else 0.0
        
        # Tech stack
        tech_kw = ["api", "cloud", "saas", "ai", "ml", "automation"]
        features["tech_stack_count"] = sum(
            1 for kw in tech_kw if kw in company_text
        )
        
        # Pain point match
        pain_points = product_analysis.get("pain_points", [])
        features["pain_point_match"] = sum(
            1 for pp in pain_points if pp.lower() in company_text
        ) / max(len(pain_points), 1)
        
        return features
    
    def predict(self, lead: Dict, product_analysis: Dict) -> Dict:
        """
        Predict lead score with SHAP explanation
        """
        
        if self.model is None:
            return self._fallback_scoring(lead, product_analysis)
        
        # Extract features
        features_dict = self.extract_features(lead, product_analysis)
        
        # Convert to array
        feature_array = np.array([[features_dict[name] for name in self.feature_names]])
        
        # Scale
        if self.scaler:
            feature_array = self.scaler.transform(feature_array)
        
        # Predict
        dmatrix = xgb.DMatrix(feature_array, feature_names=self.feature_names)
        score = float(self.model.predict(dmatrix)[0])
        
        # Confidence (distance from 0.5 decision boundary)
        confidence = abs(score - 0.5) * 2
        
        # SHAP explanation
        top_factors = []
        try:
            explainer = shap.TreeExplainer(self.model)
            shap_values = explainer.shap_values(feature_array)
            
            # Top factors
            top_factors = self._get_top_factors(shap_values[0], features_dict)
        except Exception as e:
            print(f"SHAP error: {e}")
            # Fallback: generate rule-based explanations from feature values
            top_factors = self._get_feature_based_factors(features_dict)
        
        return {
            "score": float(score),
            "confidence": float(confidence),
            "top_factors": top_factors,
            "model_version": 1
        }
    
    def _get_top_factors(self, shap_values: np.ndarray, 
                         features_dict: Dict) -> List[Dict]:
        """Extract top 5 contributing factors"""
        
        factors = []
        for i, feature_name in enumerate(self.feature_names):
            factors.append({
                "name": self._humanize(feature_name),
                "impact": float(shap_values[i]),
                "value": features_dict[feature_name]
            })
        
        factors.sort(key=lambda x: abs(x["impact"]), reverse=True)
        return factors[:5]
    
    def _get_feature_based_factors(self, features_dict: Dict) -> List[Dict]:
        """Generate explanation factors from feature values when SHAP fails"""
        factors = []
        
        # Define feature weights for importance (rough importance order)
        feature_weights = {
            "keyword_match_score": 0.20,
            "industry_relevance": 0.18,
            "contact_completeness": 0.15,
            "pain_point_match": 0.12,
            "email_available": 0.10,
            "tech_stack_count": 0.08,
            "has_funding_mention": 0.05,
            "linkedin_available": 0.04,
            "has_https": 0.03,
            "description_length_log": 0.03,
            "company_size_log": 0.02
        }
        
        for feature_name in self.feature_names:
            value = features_dict.get(feature_name, 0)
            weight = feature_weights.get(feature_name, 0.05)
            # Impact = value * weight (positive if value > 0.5, negative otherwise)
            impact = value * weight if value > 0 else -weight * 0.5
            
            factors.append({
                "name": self._humanize(feature_name),
                "impact": float(impact),
                "value": float(value) if isinstance(value, (int, float)) else 0.0
            })
        
        factors.sort(key=lambda x: abs(x["impact"]), reverse=True)
        return factors[:5]
    
    def _humanize(self, feature_name: str) -> str:
        """Convert feature name to human-readable"""
        name_map = {
            "keyword_match_score": "Keyword Match",
            "company_size_log": "Company Size",
            "industry_relevance": "Industry Fit",
            "contact_completeness": "Contact Info",
            "email_available": "Email Found",
            "linkedin_available": "LinkedIn Profile",
            "has_https": "Secure Website",
            "description_length_log": "Description Quality",
            "has_funding_mention": "Funding History",
            "tech_stack_count": "Tech Stack Match",
            "pain_point_match": "Pain Point Match"
        }
        return name_map.get(feature_name, feature_name.replace("_", " ").title())
    
    def _fallback_scoring(self, lead: Dict, product_analysis: Dict) -> Dict:
        """Rule-based fallback when ML model unavailable"""
        
        features = self.extract_features(lead, product_analysis)
        
        score = (
            features["keyword_match_score"] * 0.25 +
            features["industry_relevance"] * 0.20 +
            features["contact_completeness"] * 0.20 +
            features["pain_point_match"] * 0.15 +
            features["email_available"] * 0.10 +
            (features["tech_stack_count"] / 8.0) * 0.10
        )
        
        return {
            "score": float(min(score, 1.0)),
            "confidence": 0.5,
            "top_factors": [{"name": "Rule-based", "impact": score, "value": 1.0}],
            "model_version": 0
        }
