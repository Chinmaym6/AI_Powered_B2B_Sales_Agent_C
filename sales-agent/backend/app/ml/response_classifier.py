from transformers import pipeline
from typing import Dict
import re

class ResponseClassifier:
    """Classify email responses using BERT sentiment analysis"""
    
    def __init__(self):
        try:
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
        except Exception as e:
            print(f"Error loading sentiment model: {e}")
            self.sentiment_analyzer = None
    
    def classify_response(self, email_text: str) -> Dict:
        """
        Classify email sentiment and intent
        """
        
        if not email_text or not email_text.strip():
            return self._default_response()
        
        if self.sentiment_analyzer:
            # Sentiment analysis
            try:
                result = self.sentiment_analyzer(email_text[:512])[0]
                sentiment = "positive" if result["label"] == "POSITIVE" else "negative"
                confidence = result["score"]
                
                if confidence < 0.65:
                    sentiment = "neutral"
            except Exception:
                sentiment = "neutral"
                confidence = 0.0
        else:
            sentiment = "neutral"
            confidence = 0.0
        
        # Extract intent
        intent = self._extract_intent(email_text)
        
        # Suggested action
        suggested_action = self._suggest_action(sentiment, intent)
        
        # Urgency
        urgency = self._calculate_urgency(email_text, sentiment)
        
        return {
            "sentiment": sentiment,
            "confidence": float(confidence),
            "intent": intent,
            "suggested_action": suggested_action,
            "urgency": urgency
        }
    
    def _extract_intent(self, text: str) -> str:
        """Extract specific intent from text"""
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["demo", "show me", "trial"]):
            return "interested_demo"
        elif any(word in text_lower for word in ["pricing", "cost", "price"]):
            return "interested_pricing"
        elif any(word in text_lower for word in ["not interested", "remove"]):
            return "not_interested"
        elif any(word in text_lower for word in ["later", "next quarter"]):
            return "interested_later"
        else:
            return "needs_clarification"
    
    def _suggest_action(self, sentiment: str, intent: str) -> str:
        """Suggest next action based on sentiment and intent"""
        
        if intent == "interested_demo":
            return "schedule_demo"
        elif intent == "interested_pricing":
            return "send_pricing"
        elif intent == "not_interested":
            return "mark_closed"
        elif intent == "interested_later":
            return "schedule_followup_30_days"
        elif sentiment == "positive":
            return "send_followup"
        elif sentiment == "neutral":
            return "send_value_prop"
        else:
            return "mark_low_priority"
    
    def _calculate_urgency(self, text: str, sentiment: str) -> str:
        """Calculate urgency level"""
        
        urgent_keywords = ["asap", "urgent", "immediately", "quickly", "now"]
        
        if any(kw in text.lower() for kw in urgent_keywords):
            return "high"
        elif sentiment == "positive":
            return "high"
        elif sentiment == "neutral":
            return "medium"
        else:
            return "low"
    
    def _default_response(self) -> Dict:
        return {
            "sentiment": "neutral",
            "confidence": 0.0,
            "intent": "unknown",
            "suggested_action": "wait",
            "urgency": "low"
        }
