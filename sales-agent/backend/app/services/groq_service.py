"""
Groq Service - Fast LLM API for Research Phase
===============================================
Uses Groq API (free, fast) for research tasks to save Gemini API quota.
Groq provides 14,400 requests/day FREE with very fast inference.
"""

import httpx
import json
import asyncio
from typing import Dict, Optional
import os

class GroqService:
    """Groq API service for fast LLM inference (Research phase)"""
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")  # Fast and good
        self.enabled = bool(self.api_key) and os.getenv("GROQ_ENABLED", "true").lower() == "true"
        self.timeout = 60.0  # 60 seconds timeout
        
        # Log initialization
        if self.enabled:
            print(f"⚡ Groq Service initialized:")
            print(f"   Model: {self.model}")
            print(f"   API Key: {'Set ✅' if self.api_key else 'Missing ❌'}")
        else:
            print(f"⚠️ Groq Service disabled (no API key)")
    
    async def generate(self, prompt: str, max_retries: int = 2) -> str:
        """Generate response from Groq API"""
        
        if not self.enabled:
            raise Exception("Groq is disabled - no API key set")
        
        if not self.api_key:
            raise Exception("GROQ_API_KEY not set")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2048,  # INCREASED: Allow longer email responses
        }
        
        for attempt in range(max_retries + 1):
            try:
                print(f"⚡ [GROQ] Generating with {self.model} (attempt {attempt + 1})...")
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.base_url,
                        headers=headers,
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        
                        if text:
                            print(f"✅ [GROQ] Generated {len(text)} chars")
                            return text
                        else:
                            raise Exception("Empty response from Groq")
                    
                    elif response.status_code == 429:
                        # Rate limited - wait and retry
                        print(f"⏱️ [GROQ] Rate limited, waiting...")
                        await asyncio.sleep(2)
                        continue
                    
                    else:
                        error_msg = response.json().get("error", {}).get("message", response.text)
                        raise Exception(f"Groq API error {response.status_code}: {error_msg}")
                        
            except httpx.TimeoutException:
                print(f"⏱️ [GROQ] Timeout on attempt {attempt + 1}")
                if attempt < max_retries:
                    await asyncio.sleep(1)
                    continue
                raise Exception("Groq timeout after retries")
                
            except Exception as e:
                print(f"❌ [GROQ] Error: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(1)
                    continue
                raise
        
        raise Exception("Groq generation failed")
    
    def parse_json_response(self, response: str) -> Dict:
        """Parse JSON from Groq response"""
        import re
        
        if not response:
            return {}
        
        # Clean response
        clean = response.strip()
        
        # Remove markdown code blocks
        clean = re.sub(r'```json\s*', '', clean)
        clean = re.sub(r'```\s*', '', clean)
        clean = clean.strip()
        
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            # Try to extract JSON object
            json_match = re.search(r'\{[^{}]*\}', clean, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            # Try nested JSON
            json_match = re.search(r'\{.*\}', clean, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            return {}


# Singleton instance
_groq_service: Optional[GroqService] = None

def get_groq_service() -> GroqService:
    """Get or create Groq service singleton"""
    global _groq_service
    if _groq_service is None:
        _groq_service = GroqService()
    return _groq_service
