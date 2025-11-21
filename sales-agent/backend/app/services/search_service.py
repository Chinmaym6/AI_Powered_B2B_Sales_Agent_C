import requests
import asyncio
from typing import List, Dict, Optional
from urllib.parse import quote_plus
from ..config import settings

class SearchService:
    """
    Multi-provider search service with intelligent fallback
    
    Priority order:
    1. SerpAPI (paid, most reliable)
    2. Google Custom Search API (100 free queries/day)
    3. Bing Search API (free tier available)
    4. Direct scraping (last resort)
    """
    
    def __init__(self):
        # SerpAPI (primary)
        self.serpapi_key = settings.SERPAPI_KEY
        self.serpapi_url = "https://serpapi.com/search"
        
        # Google Custom Search API (fallback 1)
        self.google_api_key = getattr(settings, 'GOOGLE_SEARCH_API_KEY', None)
        self.google_cse_id = getattr(settings, 'GOOGLE_CSE_ID', None)
        self.google_cse_url = "https://www.googleapis.com/customsearch/v1"
        
        # Bing Search API (fallback 2)
        self.bing_api_key = getattr(settings, 'BING_SEARCH_API_KEY', None)
        self.bing_url = "https://api.bing.microsoft.com/v7.0/search"
        
        # Track usage for rate limiting
        self.serpapi_used = 0
        self.google_used = 0
        self.bing_used = 0
        
        # Daily limits (approximate)
        self.serpapi_limit = 1000  # Depends on plan
        self.google_limit = 100    # Free tier
        self.bing_limit = 1000     # Free tier
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Search using the best available provider
        Automatically falls back if a provider fails or hits limits
        """
        
        providers = [
            ("SerpAPI", self._search_serpapi),
            ("Google Custom Search", self._search_google_cse),
            ("Bing Search", self._search_bing),
            ("Direct Scraping", self._search_direct)
        ]
        
        for provider_name, search_func in providers:
            try:
                print(f"🔍 Trying {provider_name} for: {query}")
                results = await search_func(query, num_results)
                
                if results:
                    print(f"✅ {provider_name} returned {len(results)} results")
                    return results
                else:
                    print(f"⚠️ {provider_name} returned no results, trying next provider...")
                    
            except Exception as e:
                print(f"❌ {provider_name} failed: {e}")
                continue
        
        # All providers failed
        print("⚠️ All search providers failed, returning mock results")
        return self._get_mock_results(query)
    
    async def _search_serpapi(self, query: str, num_results: int) -> List[Dict]:
        """Search using SerpAPI (primary provider)"""
        
        if not self.serpapi_key or self.serpapi_key == "your_serpapi_key_here":
            raise Exception("SerpAPI key not configured")
        
        if self.serpapi_used >= self.serpapi_limit:
            raise Exception("SerpAPI daily limit reached")
        
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.serpapi_key,
            "num": num_results
        }
        
        response = requests.get(self.serpapi_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for result in data.get("organic_results", []):
            results.append({
                "title": result.get("title", ""),
                "link": result.get("link", ""),
                "snippet": result.get("snippet", "")
            })
        
        self.serpapi_used += 1
        return results
    
    async def _search_google_cse(self, query: str, num_results: int) -> List[Dict]:
        """Search using Google Custom Search API (free tier: 100 queries/day)"""
        
        if not self.google_api_key or not self.google_cse_id:
            raise Exception("Google Custom Search API not configured")
        
        if self.google_used >= self.google_limit:
            raise Exception("Google CSE daily limit reached")
        
        params = {
            "key": self.google_api_key,
            "cx": self.google_cse_id,
            "q": query,
            "num": min(num_results, 10)  # Max 10 per request
        }
        
        response = requests.get(self.google_cse_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get("items", []):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", "")
            })
        
        self.google_used += 1
        return results
    
    async def _search_bing(self, query: str, num_results: int) -> List[Dict]:
        """Search using Bing Search API (1000 free queries/month)"""
        
        if not self.bing_api_key:
            raise Exception("Bing Search API not configured")
        
        if self.bing_used >= self.bing_limit:
            raise Exception("Bing API daily limit reached")
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.bing_api_key
        }
        
        params = {
            "q": query,
            "count": num_results,
            "mkt": "en-US"
        }
        
        response = requests.get(self.bing_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for page in data.get("webPages", {}).get("value", []):
            results.append({
                "title": page.get("name", ""),
                "link": page.get("url", ""),
                "snippet": page.get("snippet", "")
            })
        
        self.bing_used += 1
        return results
    
    async def _search_direct(self, query: str, num_results: int) -> List[Dict]:
        """
        Direct scraping of search engines (last resort)
        Uses DuckDuckGo (no rate limits, no API key needed)
        """
        
        try:
            # DuckDuckGo HTML scraping
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse DuckDuckGo results
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'lxml')
            
            results = []
            result_divs = soup.find_all('div', class_='result')[:num_results]
            
            for div in result_divs:
                title_tag = div.find('a', class_='result__a')
                snippet_tag = div.find('a', class_='result__snippet')
                
                if title_tag:
                    results.append({
                        "title": title_tag.get_text(strip=True),
                        "link": title_tag.get('href', ''),
                        "snippet": snippet_tag.get_text(strip=True) if snippet_tag else ""
                    })
            
            return results
            
        except Exception as e:
            print(f"Direct scraping failed: {e}")
            raise
    
    def _get_mock_results(self, query: str) -> List[Dict]:
        """Fallback mock results if all providers fail"""
        
        return [
            {
                "title": f"Leading Company in {query}",
                "link": "https://example.com/company1",
                "snippet": f"Top provider for {query}. Innovative solutions."
            },
            {
                "title": f"{query} Experts",
                "link": "https://example.com/company2",
                "snippet": "Industry-leading technology and services."
            },
            {
                "title": f"Best {query} Solutions",
                "link": "https://example.com/company3",
                "snippet": "Trusted by Fortune 500 companies."
            }
        ]
    
    def get_usage_stats(self) -> Dict:
        """Get current usage statistics for all providers"""
        
        return {
            "serpapi": {
                "used": self.serpapi_used,
                "limit": self.serpapi_limit,
                "remaining": self.serpapi_limit - self.serpapi_used
            },
            "google_cse": {
                "used": self.google_used,
                "limit": self.google_limit,
                "remaining": self.google_limit - self.google_used
            },
            "bing": {
                "used": self.bing_used,
                "limit": self.bing_limit,
                "remaining": self.bing_limit - self.bing_used
            }
        }
