import requests
import json
from typing import Dict
from ..config import settings

class GrokService:
    """X.AI Grok API wrapper as fallback for Gemini"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'GROK_API_KEY', '')
        self.url = "https://api.x.ai/v1/chat/completions"
        self.model = "grok-beta"  # or "grok-4-latest"
    
    async def generate(self, prompt: str) -> str:
        """Generate response from Grok"""
        
        if not self.api_key:
            raise Exception("Grok API key not configured")
        
        try:
            print(f"DEBUG: Sending request to Grok API...")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant for B2B sales analysis. Always respond with valid JSON when requested."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "model": self.model,
                "stream": False,
                "temperature": 0.7
            }
            
            response = requests.post(self.url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            print(f"✅ Grok API SUCCESS")
            print(f"DEBUG: Response length: {len(content)} characters")
            return content
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Grok API ERROR: {error_msg}")
            raise Exception(f"Grok API failed: {error_msg}")
    
    def parse_json_response(self, response: str) -> Dict:
        """Parse JSON from Grok response"""
        
        if not response:
            print("ERROR: Empty response to parse")
            return {}
        
        # Remove markdown code blocks if present
        import re
        clean_response = response.strip()
        clean_response = re.sub(r'```json\s*', '', clean_response)
        clean_response = re.sub(r'```\s*', '', clean_response)
        clean_response = clean_response.strip()
        
        try:
            parsed = json.loads(clean_response)
            print(f"✅ Successfully parsed JSON response")
            return parsed
        except json.JSONDecodeError as e:
            print(f"ERROR: JSON decode failed: {e}")
            print(f"Trying to extract JSON from text...")
            
            # Try to extract JSON from text
            json_match = re.search(r'\{.*\}', clean_response, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                    print(f"✅ Extracted JSON from text successfully")
                    return parsed
                except Exception as e2:
                    print(f"ERROR: Could not parse extracted JSON: {e2}")
            
            print(f"ERROR: Could not parse JSON from response")
            print(f"Response was: {clean_response[:500]}...")
            return {}
