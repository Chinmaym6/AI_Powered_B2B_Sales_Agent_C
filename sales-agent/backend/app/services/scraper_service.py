import asyncio
import re
from typing import Dict, Optional, List
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

class ScraperService:
    """Advanced web scraping service for company data with dual-strategy approach"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.timeout = 15000  # 15 seconds for Playwright
        self.request_timeout = 10  # 10 seconds for requests
    
    async def scrape_website(self, url: str) -> Optional[Dict]:
        """
        Scrape company website using intelligent strategy selection
        1. Try fast static scraping first (requests + BeautifulSoup)
        2. Fall back to Playwright for JavaScript-heavy sites
        """
        
        try:
            # Normalize URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Try static scraping first (faster)
            result = await self._scrape_static(url)
            
            # If static scraping didn't get much data or missed email, try dynamic
            if result and (not result.get('description') or not result.get('email')):
                print(f"Static scraping incomplete (missing desc or email) for {url}, trying Playwright...")
                dynamic_result = await self._scrape_dynamic(url)
                if dynamic_result:
                    # Merge results, preferring dynamic data but keeping existing valid data
                    # If dynamic has email and static didn't, this will add it
                    for key, value in dynamic_result.items():
                        if value and (not result.get(key) or len(str(value)) > len(str(result.get(key, '')))):
                            result[key] = value
            
            return result
            
        except Exception as e:
            print(f"Scraping error for {url}: {str(e)}")
            return None
    
    async def _scrape_static(self, url: str) -> Optional[Dict]:
        """Fast scraping for static websites using requests + BeautifulSoup"""
        
        try:
            response = requests.get(url, headers=self.headers, timeout=self.request_timeout, allow_redirects=True)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract data from main page
            data = {
                "description": self._extract_description(soup),
                "industry": self._extract_industry(soup),
                "email": self._extract_email(response.text, soup),
                "linkedin": self._extract_linkedin(soup, url),
                "size": self._estimate_size(soup),
                "decision_makers": self._extract_decision_makers(soup)
            }
            
            # Deep scraping: Check sub-pages for more info if needed
            # We always check sub-pages now to get a better "full picture" for relevance checking
            subpages_content = await self._scrape_subpages(url, soup)
            if subpages_content:
                data["full_content"] = (data.get("description", "") + "\n\n" + subpages_content)[:5000] # Limit total context
                
                # Try to find email again in subpages if missing
                if not data["email"]:
                    data["email"] = self._extract_email(subpages_content, None)
            
            return data
            
        except Exception as e:
            print(f"Static scraping failed for {url}: {e}")
            return None
    
    async def _scrape_dynamic(self, url: str) -> Optional[Dict]:
        """Advanced scraping for JavaScript-heavy sites using Playwright"""
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=self.headers['User-Agent'],
                    viewport={'width': 1920, 'height': 1080}
                )
                page = await context.new_page()
                
                # Navigate and wait for content
                await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
                
                # Wait a bit for dynamic content to load
                await page.wait_for_timeout(2000)
                
                # Get the rendered HTML
                content = await page.content()
                soup = BeautifulSoup(content, 'lxml')
                
                # Extract data from rendered page
                data = {
                    "description": self._extract_description(soup),
                    "industry": self._extract_industry(soup),
                    "email": self._extract_email(content, soup),
                    "linkedin": self._extract_linkedin(soup, url),
                    "size": self._estimate_size(soup),
                    "decision_makers": self._extract_decision_makers(soup)
                }
                
                # Basic sub-page checking for dynamic sites (simulated by just checking links, not full crawl to save resources)
                # For dynamic sites, full crawling is very expensive. We'll rely on main page + static crawl of subpages if possible.
                
                await browser.close()
                return data
                
        except PlaywrightTimeout:
            print(f"Playwright timeout for {url}")
            return None
        except Exception as e:
            print(f"Dynamic scraping failed for {url}: {e}")
            return None

    async def _scrape_subpages(self, base_url: str, soup: BeautifulSoup) -> str:
        """Scrape relevant sub-pages (About, Services, Contact) to gather more context"""
        
        relevant_keywords = ['about', 'service', 'product', 'solution', 'contact', 'career', 'team']
        links_to_visit = []
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text().lower()
            
            # Check if link is relevant and internal
            if any(kw in text or kw in href.lower() for kw in relevant_keywords):
                full_url = urljoin(base_url, href)
                if urlparse(full_url).netloc == urlparse(base_url).netloc:
                    if full_url not in links_to_visit and full_url != base_url:
                        links_to_visit.append(full_url)
        
        # Limit to 3 sub-pages
        links_to_visit = links_to_visit[:3]
        aggregated_text = ""
        
        for link in links_to_visit:
            try:
                # Use requests for speed on sub-pages
                resp = requests.get(link, headers=self.headers, timeout=5)
                if resp.status_code == 200:
                    sub_soup = BeautifulSoup(resp.text, 'lxml')
                    # Extract main text
                    text = sub_soup.get_text(separator=' ', strip=True)
                    # Clean up whitespace
                    text = re.sub(r'\s+', ' ', text)
                    aggregated_text += f"\n--- Content from {link} ---\n{text[:1000]}"
            except:
                continue
                
        return aggregated_text
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract company description using multiple strategies"""
        
        # Strategy 1: Schema.org markup
        schema_desc = soup.find('script', type='application/ld+json')
        if schema_desc:
            try:
                import json
                data = json.loads(schema_desc.string)
                if isinstance(data, dict) and 'description' in data:
                    return data['description']
            except:
                pass
        
        # Strategy 2: Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content']
        
        # Strategy 3: Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content']
        
        # Strategy 4: Twitter description
        tw_desc = soup.find('meta', attrs={'name': 'twitter:description'})
        if tw_desc and tw_desc.get('content'):
            return tw_desc['content']
        
        # Strategy 5: About section
        about_keywords = ['about', 'about-us', 'company', 'overview', 'who-we-are']
        for keyword in about_keywords:
            about_section = soup.find(['section', 'div', 'article'], class_=re.compile(keyword, re.I))
            if about_section:
                text = about_section.get_text(separator=' ', strip=True)
                # Get first paragraph or first 500 chars
                paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) > 50]
                if paragraphs:
                    return paragraphs[0][:500]
        
        # Strategy 6: First substantial paragraph
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 100:  # Substantial paragraph
                return text[:500]
        
        # Strategy 7: H1 + first text
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)[:500]
        
        return ""
    
    def _extract_industry(self, soup: BeautifulSoup) -> str:
        """Identify industry using keyword matching and schema.org"""
        
        # Try schema.org first
        schema_tag = soup.find('script', type='application/ld+json')
        if schema_tag:
            try:
                import json
                data = json.loads(schema_tag.string)
                if isinstance(data, dict) and 'industry' in data:
                    return data['industry']
            except:
                pass
        
        text = soup.get_text().lower()
        
        # Extended industry detection
        industries = {
            'Technology': ['saas', 'software', 'tech', 'ai', 'machine learning', 'cloud computing', 'cybersecurity'],
            'E-commerce': ['ecommerce', 'e-commerce', 'online store', 'marketplace', 'retail'],
            'Fintech': ['fintech', 'financial technology', 'payments', 'banking', 'cryptocurrency', 'blockchain'],
            'Healthcare': ['healthcare', 'medical', 'health tech', 'telemedicine', 'pharma', 'biotech'],
            'Marketing': ['marketing', 'advertising', 'martech', 'digital marketing', 'seo', 'content marketing'],
            'SaaS': ['software as a service', 'subscription software', 'b2b software', 'enterprise software'],
            'Manufacturing': ['manufacturing', 'production', 'industrial', 'factory'],
            'Logistics': ['logistics', 'supply chain', 'shipping', 'transportation', 'freight'],
            'Education': ['edtech', 'education', 'learning', 'training', 'e-learning'],
            'Real Estate': ['real estate', 'property', 'proptech', 'realty']
        }
        
        for industry, keywords in industries.items():
            if any(kw in text for kw in keywords):
                return industry
        
        return "Other"
    
    def _extract_email(self, text: str, soup: BeautifulSoup) -> Optional[str]:
        """Extract contact email with smart filtering"""
        
        # Find all emails
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        
        # Extract from mailto links if soup provided
        if soup:
            mailto_links = soup.select('a[href^="mailto:"]')
            for link in mailto_links:
                href = link.get('href', '')
                if ':' in href:
                    email = href.split(':')[1].split('?')[0]
                    if email:
                        emails.append(email)
        
        # Decode obfuscated emails (common pattern: email [at] domain [dot] com)
        obfuscated = re.findall(r'([\w\.\-]+)\s*\[at\]\s*([\w\.\-]+)\s*\[dot\]\s*(\w+)', text.lower())
        for user, domain, tld in obfuscated:
            emails.append(f"{user}@{domain}.{tld}")
        
        # Filter out invalid emails
        ignore_patterns = [
            'example.com', 'yourdomain.com', 'test@', 'no-reply', 'noreply',
            'image@', 'support@github', 'privacy@', 'legal@', '@placeholder',
            '@example', 'feedback@', 'abuse@'
        ]
        
        # Image/file extensions that are NOT valid emails
        invalid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.pdf', '.doc', '.docx']
        
        valid_emails = []
        for email in emails:
            email_lower = email.lower()
            
            # Skip if matches ignore patterns
            if any(pattern in email_lower for pattern in ignore_patterns):
                continue
            
            # Skip if it looks like a file (contains file extensions)
            if any(ext in email_lower for ext in invalid_extensions):
                continue
                
            # Skip if email is too long or contains suspicious characters
            if len(email) > 100 or email.count('@') != 1:
                continue
            
            # Basic format validation: must have @ and a dot after @
            parts = email.split('@')
            if len(parts) == 2 and '.' in parts[1]:
                valid_emails.append(email)
        
        if not valid_emails:
            return None
        
        # Prioritize contact-related emails
        priority_prefixes = ['contact', 'info', 'hello', 'sales', 'support', 'inquiry', 'business']
        for email in valid_emails:
            email_lower = email.lower()
            if any(prefix in email_lower for prefix in priority_prefixes):
                return email
        
        # Return first valid email
        return valid_emails[0]
    
    def _extract_linkedin(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract LinkedIn company profile URL"""
        
        # Find all links
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '')
            
            # Check if it's a LinkedIn company URL
            if 'linkedin.com' in href and '/company/' in href:
                # Clean up URL
                if href.startswith('//'):
                    href = 'https:' + href
                elif not href.startswith('http'):
                    href = urljoin(base_url, href)
                
                return href
        
        return None
    
    def _estimate_size(self, soup: BeautifulSoup) -> int:
        """Estimate company size from various signals"""
        
        text = soup.get_text().lower()
        
        # Look for explicit mentions
        size_patterns = [
            (r'(\d+[\+]?)\s*employees', 1),
            (r'team of\s*(\d+)', 1),
            (r'staff of\s*(\d+)', 1),
            (r'(\d+)[\+]?\s*people', 1),
        ]
        
        for pattern, group in size_patterns:
            match = re.search(pattern, text)
            if match:
                size_str = match.group(group).replace('+', '')
                try:
                    return int(size_str)
                except:
                    pass
        
        # Heuristic-based estimation
        if any(word in text for word in ['fortune 500', 'enterprise', 'global leader', 'multinational']):
            return 5000
        elif any(word in text for word in ['startup', 'founded in 202', 'early stage']):
            return 25
        elif any(word in text for word in ['growing team', 'scaling', 'series a', 'series b']):
            return 100
        
        # Default to small-medium
        return 50
    
    def _extract_decision_makers(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract decision-maker information from team/about pages"""
        
        decision_makers = []
        
        # Look for team sections
        team_sections = soup.find_all(['section', 'div'], class_=re.compile(r'team|leadership|about|executives', re.I))
        
        for section in team_sections:
            # Look for person cards
            person_cards = section.find_all(['div', 'article'], class_=re.compile(r'person|member|profile|card', re.I))
            
            for card in person_cards[:5]:  # Limit to first 5
                name_tag = card.find(['h3', 'h4', 'h5', 'p'], class_=re.compile(r'name', re.I))
                title_tag = card.find(['p', 'span', 'div'], class_=re.compile(r'title|role|position', re.I))
                
                if name_tag:
                    name = name_tag.get_text(strip=True)
                    title = title_tag.get_text(strip=True) if title_tag else ""
                    
                    # Only include C-level, founders, VPs, directors
                    if any(keyword in title.lower() for keyword in ['ceo', 'cto', 'cfo', 'founder', 'vp', 'director', 'head', 'chief']):
                        decision_makers.append({
                            "name": name,
                            "title": title
                        })
        
        return decision_makers[:3]  # Return top 3
    
    def extract_company_name_from_url(self, url: str) -> str:
        """Extract likely company name from URL"""
        
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        
        # Remove TLD
        name = domain.split('.')[0]
        
        # Capitalize properly
        return name.replace('-', ' ').replace('_', ' ').title()
