"""
Sentiment Analysis Service using Gemini AI
Analyzes email replies to determine sentiment, intent, and automatically label leads
"""

from typing import Dict
from ..services.gemini_service import GeminiService
import re


class SentimentService:
    """AI-powered sentiment analysis for email replies using Gemini"""
    
    def __init__(self):
        self.gemini = GeminiService()
    
    async def analyze_reply(self, reply_text: str, original_email: str = "") -> Dict:
        """
        Analyze email reply sentiment and intent using Gemini AI
        
        Args:
            reply_text: The email reply content
            original_email: The original email sent (optional, for context)
        
        Returns:
            {
                'sentiment': 'positive'/'negative'/'neutral',
                'confidence': 0.85,  # 0-1
                'intent': 'interested_demo'/'not_interested'/etc.,
                'should_auto_label': True/False,
                'suggested_outcome': 1/0/None,
                'explanation': 'They expressed strong interest...'
            }
        """
        
        # Clean the reply text
        cleaned_text = self._clean_email_text(reply_text)
        
        if not cleaned_text or len(cleaned_text) < 10:
            return self._default_response("Email too short or empty")
        
        # Prompt for Gemini
        prompt = f"""You are an expert email sentiment analyzer for B2B sales.

Analyze this email reply and determine:
1. **Sentiment**: Is the overall tone positive, negative, or neutral?
2. **Intent**: What does the person want? (interested_demo, interested_pricing, not_interested, needs_more_info, interested_later, etc.)
3. **Confidence**: How confident are you in your assessment? (0.0 to 1.0)
4. **Auto-label**: Should this lead be automatically labeled as good (1) or bad (0) based on clear signals?

ORIGINAL EMAIL CONTEXT (if available):
{original_email[:200] if original_email else 'N/A'}

REPLY TO ANALYZE:
{cleaned_text}

RULES FOR AUTO-LABELING:
- Only auto-label if confidence >= 0.75
- Positive sentiment + high confidence = good lead (outcome = 1)
- Negative sentiment + clear rejection = bad lead (outcome = 0)
- If ambiguous or neutral = don't auto-label (outcome = null)

Return ONLY valid JSON:
{{
  "sentiment": "positive/negative/neutral",
  "confidence": 0.85,
  "intent": "interested_demo",
  "should_auto_label": true,
  "suggested_outcome": 1,
  "explanation": "Clear expression of interest in seeing a demo"
}}
"""
        
        try:
            response = await self.gemini.generate(prompt)
            parsed = self.gemini.parse_json_response(response)
            
            if not parsed:
                return self._default_response("Failed to parse AI response")
            
            # Validate and return
            return {
                'sentiment': parsed.get('sentiment', 'neutral'),
                'confidence': float(parsed.get('confidence', 0.0)),
                'intent': parsed.get('intent', 'unknown'),
                'should_auto_label': parsed.get('should_auto_label', False),
                'suggested_outcome': parsed.get('suggested_outcome'),  # 1, 0, or None
                'explanation': parsed.get('explanation', '')
            }
            
        except Exception as e:
            print(f"Sentiment analysis error: {e}")
            return self._default_response(f"Analysis failed: {str(e)}")
    
    def _clean_email_text(self, text: str) -> str:
        """Remove email signatures, quoted text, and clean formatting"""
        
        # Remove quoted text (lines starting with >)
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip quoted lines
            if line.strip().startswith('>'):
                continue
            # Skip common signature markers
            if line.strip() in ['--', '___', 'Sent from my iPhone', 'Sent from my Android']:
                break
            # Skip lines with just dashes or equals
            if re.match(r'^[\-=_]{3,}$', line.strip()):
                continue
            
            cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # Remove multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove excessive whitespace
        text = re.sub(r' {2,}', ' ', text)
        
        return text.strip()
    
    def _default_response(self, reason: str = "") -> Dict:
        """Return default response when analysis fails"""
        return {
            'sentiment': 'neutral',
            'confidence': 0.0,
            'intent': 'unknown',
            'should_auto_label': False,
            'suggested_outcome': None,
            'explanation': reason or 'Unable to analyze'
        }
    
    def classify_intent_keywords(self, text: str) -> str:
        """
        Fallback keyword-based intent classification
        (Used as backup if Gemini fails)
        """
        
        text_lower = text.lower()
        
        # Positive interest
        if any(word in text_lower for word in ['demo', 'show me', 'trial', 'let\'s talk', 'interested', 'call', 'schedule']):
            return 'interested_demo'
        
        # Pricing inquiry
        if any(word in text_lower for word in ['pricing', 'cost', 'price', 'how much', 'quote']):
            return 'interested_pricing'
        
        # Clear rejection
        if any(word in text_lower for word in ['not interested', 'remove me', 'unsubscribe', 'stop sending', 'no thanks']):
            return 'not_interested'
        
        # Delay
        if any(word in text_lower for word in ['later', 'next quarter', 'next year', 'not right now', 'busy']):
            return 'interested_later'
        
        # Needs more info
        if any(word in text_lower for word in ['more information', 'tell me more', 'send me', 'can you', 'what is']):
            return 'needs_more_info'
        
        return 'unknown'
