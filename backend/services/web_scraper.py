"""Web scraping service for competitive intelligence"""
import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, List, Any
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class WebScraperService:
    """Service for scraping competitive intelligence from web"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.timeout = 10
    
    def scrape_competitor_website(self, company_name: str, website_url: str) -> Dict[str, Any]:
        """Scrape competitor website for intelligence"""
        try:
            response = requests.get(website_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            data = {
                'company_name': company_name,
                'website': website_url,
                'scraped_at': datetime.utcnow().isoformat(),
                'title': soup.title.string if soup.title else 'N/A',
                'meta_description': self._extract_meta_description(soup),
                'pricing_info': self._extract_pricing(soup),
                'features': self._extract_features(soup),
                'messaging': self._extract_messaging(soup),
                'call_to_actions': self._extract_ctas(soup),
                'contact_info': self._extract_contact_info(soup)
            }
            return data
        except Exception as e:
            logger.error(f"Error scraping {website_url}: {e}")
            return {'error': str(e), 'company_name': company_name}
    
    def scrape_g2_reviews(self, company_name: str) -> Dict[str, Any]:
        """Scrape G2 reviews for sentiment and feedback"""
        # This is a placeholder - actual G2 scraping would need more sophisticated handling
        try:
            # In production, you'd use a G2 API or more advanced scraping
            g2_url = f"https://www.g2.com/products/{company_name.lower()}/reviews"
            
            data = {
                'company_name': company_name,
                'source': 'G2',
                'reviews_summary': 'N/A - Requires API access',
                'average_rating': 0.0,
                'total_reviews': 0,
                'sentiment_analysis': {
                    'positive': [],
                    'negative': [],
                    'neutral': []
                }
            }
            return data
        except Exception as e:
            logger.error(f"Error scraping G2 for {company_name}: {e}")
            return {}
    
    def scrape_reddit_discussions(self, company_name: str) -> List[Dict]:
        """Scrape Reddit for community discussions and sentiment"""
        try:
            discussions = [
                {
                    'platform': 'Reddit',
                    'company': company_name,
                    'discussion_count': 0,
                    'key_topics': [],
                    'sentiment_summary': 'N/A - Requires Reddit API'
                }
            ]
            return discussions
        except Exception as e:
            logger.error(f"Error scraping Reddit for {company_name}: {e}")
            return []
    
    def scrape_linkedin_updates(self, company_name: str) -> Dict[str, Any]:
        """Scrape LinkedIn for company updates and announcements"""
        try:
            data = {
                'company_name': company_name,
                'source': 'LinkedIn',
                'recent_posts': [],
                'company_updates': [],
                'employee_insights': []
            }
            return data
        except Exception as e:
            logger.error(f"Error scraping LinkedIn for {company_name}: {e}")
            return {}
    
    def scrape_pricing_page(self, pricing_url: str) -> Dict[str, Any]:
        """Parse pricing page for pricing strategy"""
        try:
            response = requests.get(pricing_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            pricing_data = {
                'url': pricing_url,
                'tiers': self._parse_pricing_tiers(soup),
                'features_by_tier': self._parse_features_by_tier(soup),
                'cta_text': self._extract_ctas(soup)
            }
            return pricing_data
        except Exception as e:
            logger.error(f"Error scraping pricing from {pricing_url}: {e}")
            return {}
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        meta = soup.find('meta', attrs={'name': 'description'})
        return meta['content'] if meta and meta.get('content') else 'N/A'
    
    def _extract_pricing(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract pricing information from page"""
        pricing = []
        # Look for common pricing patterns
        price_sections = soup.find_all(['div', 'section'], class_=lambda x: x and 'pricing' in x.lower())
        
        for section in price_sections[:5]:  # Limit to 5
            pricing.append(section.get_text(strip=True)[:200])
        
        return pricing
    
    def _extract_features(self, soup: BeautifulSoup) -> List[str]:
        """Extract feature mentions from page"""
        features = []
        
        # Look for feature sections
        feature_sections = soup.find_all(['li', 'span'], class_=lambda x: x and 'feature' in x.lower())
        
        for feature in feature_sections[:10]:
            text = feature.get_text(strip=True)
            if text and len(text) > 5 and len(text) < 200:
                features.append(text)
        
        return list(set(features))  # Remove duplicates
    
    def _extract_messaging(self, soup: BeautifulSoup) -> List[str]:
        """Extract key messaging from page"""
        messaging = []
        
        # Look for h1, h2, h3 tags for main messaging
        for tag in soup.find_all(['h1', 'h2', 'h3'])[:10]:
            text = tag.get_text(strip=True)
            if text and len(text) > 10 and len(text) < 300:
                messaging.append(text)
        
        return messaging
    
    def _extract_ctas(self, soup: BeautifulSoup) -> List[str]:
        """Extract call-to-action text"""
        ctas = []
        
        # Look for button and link text
        for button in soup.find_all(['button', 'a'], class_=lambda x: x and 'cta' in x.lower())[:5]:
            text = button.get_text(strip=True)
            if text and len(text) < 100:
                ctas.append(text)
        
        return ctas
    
    def _extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract contact information"""
        contact = {
            'email': 'N/A',
            'phone': 'N/A',
            'address': 'N/A'
        }
        
        # Look for email
        footer = soup.find('footer')
        if footer:
            text = footer.get_text(strip=True)
            if '@' in text:
                emails = [word for word in text.split() if '@' in word]
                if emails:
                    contact['email'] = emails[0]
        
        return contact
    
    def _parse_pricing_tiers(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse pricing tier information"""
        tiers = []
        
        # Look for pricing cards
        tier_cards = soup.find_all(['div', 'article'], class_=lambda x: x and 'tier' in x.lower() or 'plan' in x.lower())
        
        for card in tier_cards[:5]:
            tier_info = {
                'name': card.get_text(strip=True)[:50],
                'price': 'N/A'
            }
            tiers.append(tier_info)
        
        return tiers
    
    def _parse_features_by_tier(self, soup: BeautifulSoup) -> Dict:
        """Parse features organized by pricing tier"""
        # This would need more sophisticated parsing based on actual page structure
        return {}
    
    def aggregate_competitor_data(self, company_name: str, website: str, 
                                  additional_sources: List[str] = None) -> Dict[str, Any]:
        """Aggregate data from multiple sources for a competitor"""
        data = {
            'company_name': company_name,
            'aggregated_at': datetime.utcnow().isoformat(),
            'sources': []
        }
        
        # Scrape website
        website_data = self.scrape_competitor_website(company_name, website)
        data['website_analysis'] = website_data
        data['sources'].append('website')
        
        # Scrape pricing if available
        if 'pricing' in website or '/pricing' in website:
            pricing_data = self.scrape_pricing_page(website + '/pricing' if not 'pricing' in website else website)
            data['pricing_analysis'] = pricing_data
            data['sources'].append('pricing_page')
        
        # Scrape G2
        g2_data = self.scrape_g2_reviews(company_name)
        data['g2_reviews'] = g2_data
        data['sources'].append('g2')
        
        # Scrape Reddit
        reddit_data = self.scrape_reddit_discussions(company_name)
        data['reddit_discussions'] = reddit_data
        data['sources'].append('reddit')
        
        # Scrape LinkedIn
        linkedin_data = self.scrape_linkedin_updates(company_name)
        data['linkedin_updates'] = linkedin_data
        data['sources'].append('linkedin')
        
        return data
