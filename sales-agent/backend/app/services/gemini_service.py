from google import genai
import json
import re
from typing import Dict
from ..config import settings

class GeminiService:
    """Wrapper for Google Gemini API using the new google-genai SDK"""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key or self.api_key == "":
            print("WARNING: Gemini API key not configured!")
            self.client = None
        else:
            # Initialize the new genai client
            self.client = genai.Client(api_key=self.api_key)
        
        # Use gemini-2.5-flash (the latest model)
        self.model = "gemini-2.5-flash"
    
    async def generate(self, prompt: str, max_retries: int = 3) -> str:
        """Generate response from Gemini using new SDK with retry logic"""
        
        if not self.client:
            raise Exception("Gemini API key not configured")
        
        retry_count = 0
        while retry_count <= max_retries:
            try:
                print(f"DEBUG: Sending request to Gemini API... (Attempt {retry_count + 1}/{max_retries + 1})")
                print(f"DEBUG: Model: {self.model}")
                print(f"DEBUG: Prompt length: {len(prompt)} characters")
                
                # Use the new SDK
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                
                # Extract text from response
                text = response.text
                
                if not text:
                    print(f"ERROR: Gemini returned empty response")
                    raise Exception("Empty response from Gemini")
                
                print(f"✅ Gemini API SUCCESS")
                print(f"DEBUG: Response length: {len(text)} characters")
                print(f"DEBUG: Gemini Response Preview: {text[:200]}...")
                return text
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Gemini API ERROR: {error_msg}")
                
                # Check for specific error types
                if "API_KEY_INVALID" in error_msg or "401" in error_msg:
                    print("ERROR: Your Gemini API key is invalid!")
                    raise Exception(f"Gemini API failed: {error_msg}")
                
                elif "quota" in error_msg.lower() or "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    print(f"⚠️ Gemini API quota exceeded! Waiting 6 seconds before retry...")
                    if retry_count < max_retries:
                        import asyncio
                        await asyncio.sleep(6)  # Wait 6 seconds to respect rate limits
                        retry_count += 1
                        continue
                    else:
                        print("❌ Max retries reached. Quota exhausted.")
                        raise Exception(f"Gemini API quota exhausted after {max_retries} retries")
                
                elif "403" in error_msg:
                    print("ERROR: Forbidden - check API key permissions!")
                    raise Exception(f"Gemini API failed: {error_msg}")
                elif "404" in error_msg or "not found" in error_msg.lower():
                    print("ERROR: Gemini model not found!")
                    raise Exception(f"Gemini API failed: {error_msg}")
                else:
                    # For other errors, retry once
                    if retry_count < max_retries:
                        import asyncio
                        await asyncio.sleep(2)
                        retry_count += 1
                        continue
                    raise Exception(f"Gemini API failed: {error_msg}")
    
    def parse_json_response(self, response: str) -> Dict:
        """Parse JSON from Gemini response"""
        
        if not response:
            print("ERROR: Empty response to parse")
            return {}
            
        # Remove markdown code blocks if present
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
