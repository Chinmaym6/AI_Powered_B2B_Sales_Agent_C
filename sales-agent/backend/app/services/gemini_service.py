from google import genai
import json
import re
from typing import Dict
from ..config import settings

class GeminiService:
    """Wrapper for Google Gemini API with Groq fallback"""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key or self.api_key == "":
            print("WARNING: Gemini API key not configured!")
            self.client = None
        else:
            # Initialize the new genai client
            self.client = genai.Client(api_key=self.api_key)
        
        # Model selection via env var (default: gemini-2.0-flash)
        import os
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        print(f"🤖 Gemini Model: {self.model}")
        
        # Initialize Groq as fallback
        self.groq = None
        self._init_groq_fallback()
    
    def _init_groq_fallback(self):
        """Initialize Groq service as fallback"""
        try:
            from .groq_service import get_groq_service
            self.groq = get_groq_service()
            if self.groq.enabled:
                print("🔄 Groq fallback enabled for Gemini")
            else:
                self.groq = None
        except Exception as e:
            print(f"⚠️ Groq fallback not available: {e}")
            self.groq = None
    
    async def generate(self, prompt: str, max_retries: int = 3) -> str:
        """Generate response from Gemini with Groq fallback on quota exhaustion"""
        
        if not self.client:
            # No Gemini, try Groq directly
            if self.groq and self.groq.enabled:
                print("⚠️ Gemini not configured, using Groq")
                return await self.groq.generate(prompt)
            raise Exception("Gemini API key not configured and no fallback available")
        
        retry_count = 0
        gemini_failed = False
        
        while retry_count <= max_retries:
            try:
                print(f"🤖 [GEMINI] Sending request... (Attempt {retry_count + 1}/{max_retries + 1})")
                
                # Use the new SDK
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                
                # Extract text from response
                text = response.text
                
                if not text:
                    raise Exception("Empty response from Gemini")
                
                print(f"✅ [GEMINI] Success - {len(text)} chars")
                return text
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ [GEMINI] Error: {error_msg[:100]}")
                
                # Check for quota exhaustion
                if "quota" in error_msg.lower() or "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    print(f"⚠️ [GEMINI] Quota exceeded!")
                    
                    if retry_count < max_retries:
                        import asyncio
                        await asyncio.sleep(6)
                        retry_count += 1
                        continue
                    else:
                        gemini_failed = True
                        break
                
                # Check for invalid API key
                elif "API_KEY_INVALID" in error_msg or "401" in error_msg:
                    gemini_failed = True
                    break
                
                # Other errors
                else:
                    if retry_count < max_retries:
                        import asyncio
                        await asyncio.sleep(2)
                        retry_count += 1
                        continue
                    gemini_failed = True
                    break
        
        # Gemini failed - try Groq fallback
        if gemini_failed and self.groq and self.groq.enabled:
            print("🔄 [FALLBACK] Switching to Groq...")
            try:
                result = await self.groq.generate(prompt)
                print(f"✅ [GROQ FALLBACK] Success - {len(result)} chars")
                return result
            except Exception as groq_error:
                print(f"❌ [GROQ FALLBACK] Also failed: {groq_error}")
                raise Exception(f"Both Gemini and Groq failed. Gemini: quota exhausted. Groq: {groq_error}")
        
        raise Exception("Gemini API failed and no fallback available")
    
    def parse_json_response(self, response: str) -> Dict:
        """Parse JSON from Gemini response"""
        
        if not response:
            return {}
            
        # Remove markdown code blocks if present
        clean_response = response.strip()
        clean_response = re.sub(r'```json\s*', '', clean_response)
        clean_response = re.sub(r'```\s*', '', clean_response)
        clean_response = clean_response.strip()
        
        try:
            return json.loads(clean_response)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            json_match = re.search(r'\{.*\}', clean_response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            return {}
