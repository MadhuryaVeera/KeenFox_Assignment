"""LLM Service for Google Gemini AI reasoning"""
import google.generativeai as genai
import json
import os
import re
import hashlib
import time
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with Google Gemini API"""
    
    def __init__(self):
        self.model = None
        self._initialized = False
        self._response_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl_seconds = int(os.getenv('LLM_CACHE_TTL_SECONDS', '1200'))
    
    def _ensure_initialized(self):
        """Initialize LLM on first use"""
        if self._initialized:
            return
        
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        self._initialized = True
    
    def extract_competitor_insights(self, competitor_name: str, raw_data: Dict[str, Any]) -> Dict:
        """Extract structured insights from competitor data"""
        prompt = f"""
Analyze the following competitive data for {competitor_name} and extract structured insights:

{json.dumps(raw_data, indent=2)}

Groundedness rules:
- Use only the provided data.
- Do not invent product details, pricing, or sentiment not present in the input.
- If evidence is missing, return conservative placeholders and keep confidence low.

Extract and return a JSON object with these exact fields:
{{
    "key_features": ["list of top 5-7 features"],
    "messaging_themes": ["key messaging themes and positioning angles"],
    "customer_sentiment": {{
        "positives": ["what customers love"],
        "negatives": ["main complaints"],
        "sentiment_score": 0.0-1.0
    }},
    "pricing_strategy": {{
        "model": "pricing model type",
        "tiers": ["tier names if applicable"],
        "price_range": "price range if available"
    }},
    "market_gaps": ["gaps or weaknesses in their offering"],
    "competitive_threats": ["main threats to KeenFox"],
    "opportunity_areas": ["areas where KeenFox can differentiate"]
}}

Return ONLY valid JSON, no other text.
"""
        try:
            insights = self._generate_json_response(
                prompt=prompt,
                cache_namespace='extract_competitor_insights',
                cache_payload={'competitor_name': competitor_name, 'raw_data': raw_data},
            )
            return self._normalize_insights(competitor_name, raw_data, insights)
        except Exception as e:
            logger.error(f"Error extracting insights for {competitor_name}: {e}")
            return self._build_fallback_insights(competitor_name, raw_data)
    
    def generate_campaign_recommendations(self, brand_name: str, 
                                         competitor_data: List[Dict],
                                         category: str = 'general_b2b') -> Dict:
        """Generate AI-powered campaign recommendations"""
        competitor_summary = "\n".join([
            (
                f"- {comp.get('competitor_name', 'Unknown')}: "
                f"{comp.get('insights', {}).get('key_features', [])} | Weaknesses: "
                f"{comp.get('insights', {}).get('market_gaps', [])}"
            )
            for comp in competitor_data
        ])
        
        prompt = f"""
You are a strategic marketing consultant. Analyze the competitive landscape for {brand_name} 
and generate actionable campaign recommendations.

Competitor Analysis Summary:
{competitor_summary}

Generate a JSON response with:
{{
    "messaging_positioning": {{
        "headline": "New homepage headline",
        "subheadline": "Supporting message",
        "value_props": ["3-5 key value propositions"],
        "differentiation": "How to differentiate from competitors",
        "ad_copy": {{
            "email": "Cold email headline and hook",
            "linkedin": "LinkedIn post content",
            "website": "Homepage CTA copy"
        }}
    }},
    "channel_strategy": {{
        "primary_channels": ["channels to focus on"],
        "secondary_channels": ["supporting channels"],
        "rationale": "Why these channels based on competitor activity"
    }},
    "gtm_recommendations": [
        {{
            "priority": "High/Medium/Low",
            "title": "Recommendation title",
            "description": "Detailed description",
            "rationale": "Why this based on competitor gaps",
            "expected_impact": "Expected business impact",
            "timeline": "Implementation timeline"
        }}
    ],
    "overall_strategy": "2-3 sentence synthesis of strategic direction"
}}

Return ONLY valid JSON, no other text.
"""
        try:
            recommendations = self._generate_json_response(
                prompt=prompt,
                cache_namespace='generate_campaign_recommendations',
                cache_payload={
                    'brand_name': brand_name,
                    'category': category,
                    'competitor_data': competitor_data,
                },
            )
            return self._normalize_recommendations(brand_name, competitor_data, recommendations, category)
        except Exception as e:
            logger.error(f"Error generating recommendations for {brand_name}: {e}")
            return self._build_fallback_recommendations(brand_name, competitor_data, category)
    
    def analyze_market_positioning(self, brand_name: str, competitors: List[Dict], category: str = 'general_b2b') -> Dict:
        """Analyze market positioning and threats"""
        prompt = f"""
Analyze the market positioning for {brand_name} against its competitors:

Competitors: {json.dumps(competitors, indent=2)}

Provide analysis in JSON format:
{{
    "market_position": "Leader/Strong Contender/Challenger/Niche",
    "threat_level": "High/Medium/Low",
    "key_threats": ["top 3-5 threats"],
    "opportunities": ["top 3-5 opportunities"],
    "competitive_advantages": ["areas where KeenFox outperforms"],
    "vulnerabilities": ["areas to address urgently"],
    "market_trends": ["relevant market trends affecting positioning"]
}}

Return ONLY valid JSON.
"""
        try:
            analysis = self._generate_json_response(
                prompt=prompt,
                cache_namespace='analyze_market_positioning',
                cache_payload={'brand_name': brand_name, 'category': category, 'competitors': competitors},
            )
            return self._normalize_market_analysis(brand_name, competitors, analysis, category)
        except Exception as e:
            logger.error(f"Error analyzing positioning for {brand_name}: {e}")
            return self._build_fallback_market_analysis(brand_name, competitors, category)

    def _generate_json_response(self, prompt: str, cache_namespace: str, cache_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JSON response with lightweight caching and strict parsing."""
        self._ensure_initialized()
        cache_key = self._build_cache_key(cache_namespace, cache_payload)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        response = self.model.generate_content(prompt)
        parsed = self._extract_json_object(getattr(response, 'text', ''))
        self._cache_set(cache_key, parsed)
        return parsed

    def _build_cache_key(self, namespace: str, payload: Dict[str, Any]) -> str:
        """Build deterministic cache key for LLM calls."""
        blob = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
        digest = hashlib.sha256(f"{namespace}:{blob}".encode('utf-8')).hexdigest()
        return f"{namespace}:{digest}"

    def _cache_get(self, key: str) -> Dict[str, Any]:
        """Read response from in-memory cache if fresh."""
        entry = self._response_cache.get(key)
        if not entry:
            return None
        if time.time() - entry['ts'] > self._cache_ttl_seconds:
            self._response_cache.pop(key, None)
            return None
        return entry['value']

    def _cache_set(self, key: str, value: Dict[str, Any]) -> None:
        """Store response in in-memory cache."""
        self._response_cache[key] = {'ts': time.time(), 'value': value}

    def discover_competitors(self, brand_name: str, category: str, limit: int = 8) -> List[str]:
        """Discover likely direct competitors dynamically for any input brand."""
        try:
            self._ensure_initialized()
            safe_limit = max(3, min(int(limit or 8), 12))
            prompt = f"""
You are a market intelligence analyst.

Brand: {brand_name}
Category hint: {category}

Return {safe_limit} likely direct competitors for this brand.
Rules:
- Prefer direct competitors (same customer problem and buying decision)
- Return only company/product names, not categories
- Do not include the input brand itself

Return ONLY valid JSON in this exact format:
{{"competitors":["Name 1","Name 2","Name 3"]}}
"""
            parsed = self._generate_json_response(
                prompt=prompt,
                cache_namespace='discover_competitors',
                cache_payload={'brand_name': brand_name, 'category': category, 'limit': safe_limit},
            )
            competitors = parsed.get('competitors', []) if isinstance(parsed, dict) else []
            cleaned = self._clean_competitor_names(brand_name, competitors)
            if cleaned:
                return cleaned[:safe_limit]

            # Retry once with a simpler instruction if JSON adherence fails.
            retry_prompt = f"""
List {safe_limit} direct competitors of {brand_name}.
Return JSON only:
{{"competitors":["name1","name2"]}}
"""
            retry_response = self.model.generate_content(retry_prompt)
            retry_parsed = self._extract_json_object(retry_response.text)
            retry_competitors = retry_parsed.get('competitors', []) if isinstance(retry_parsed, dict) else []
            cleaned = self._clean_competitor_names(brand_name, retry_competitors)
            if cleaned:
                return cleaned[:safe_limit]

            # Final fallback: attempt to parse plain text list output.
            text_names = self._extract_names_from_text(retry_response.text)
            return self._clean_competitor_names(brand_name, text_names)[:safe_limit]
        except Exception as exc:
            logger.warning(f"Dynamic competitor discovery failed for {brand_name}: {exc}")
            return []

    def validate_competitor_relevance(self, brand_name: str, category: str, competitors: List[str]) -> List[str]:
        """Guardrail check to keep only relevant competitors and filter wrong ones."""
        if not competitors:
            return []

        fallback = self._clean_competitor_names(brand_name, competitors)

        try:
            self._ensure_initialized()
            prompt = f"""
Validate whether each candidate is a relevant direct competitor.

Brand: {brand_name}
Category hint: {category}
Candidates: {json.dumps(competitors)}

Return ONLY valid JSON in this exact shape:
{{
  "approved": ["names that are true direct competitors"],
  "rejected": ["names that are wrong/weak fit"]
}}
"""
            parsed = self._generate_json_response(
                prompt=prompt,
                cache_namespace='validate_competitor_relevance',
                cache_payload={
                    'brand_name': brand_name,
                    'category': category,
                    'competitors': competitors,
                },
            )
            approved = parsed.get('approved', []) if isinstance(parsed, dict) else []
            if not isinstance(approved, list):
                return []

            cleaned = []
            brand_norm = brand_name.strip().lower()
            for name in approved:
                n = str(name).strip()
                if not n or n.lower() == brand_norm:
                    continue
                if n not in cleaned:
                    cleaned.append(n)

            if cleaned:
                return cleaned
            return fallback
        except Exception as exc:
            logger.warning(f"Competitor guardrail validation fallback for {brand_name}: {exc}")

        # Deterministic fallback guardrail when LLM validation is unavailable.
        return fallback

    def discover_company_website(self, company_name: str, category: str = 'general_b2b') -> str:
        """Infer an official company website for better scraping coverage."""
        try:
            self._ensure_initialized()
            prompt = f"""
Find the most likely official website for this company.

Company: {company_name}
Category hint: {category}

Return ONLY valid JSON in this exact format:
{{"website":"https://example.com"}}

If uncertain, return an empty website value.
"""
            parsed = self._generate_json_response(
                prompt=prompt,
                cache_namespace='discover_company_website',
                cache_payload={'company_name': company_name, 'category': category},
            )
            website = parsed.get('website', '') if isinstance(parsed, dict) else ''
            website = str(website).strip()
            if website.startswith('http://') or website.startswith('https://'):
                return website.rstrip('/')
            return ''
        except Exception as exc:
            logger.warning(f"Website discovery failed for {company_name}: {exc}")
            return ''

    @staticmethod
    def _extract_json_object(raw_text: str) -> Dict[str, Any]:
        """Extract a JSON object from plain or fenced model output."""
        text = (raw_text or '').strip()
        if '```json' in text:
            text = text.split('```json', 1)[1].split('```', 1)[0]
        elif '```' in text:
            text = text.split('```', 1)[1].split('```', 1)[0]
        parsed = json.loads(text.strip())
        return parsed if isinstance(parsed, dict) else {}

    @staticmethod
    def _clean_competitor_names(brand_name: str, names: Any) -> List[str]:
        """Normalize and de-duplicate candidate competitor names."""
        if not isinstance(names, list):
            return []

        brand_norm = (brand_name or '').strip().lower()
        blocked = {'unknown', 'n/a', 'none', 'null', 'competitor', 'brand'}
        cleaned: List[str] = []

        for raw_name in names:
            name = str(raw_name or '').strip()
            if not name:
                continue
            norm = name.lower()
            if norm == brand_norm or norm in blocked:
                continue
            if name not in cleaned:
                cleaned.append(name)

        return cleaned

    @staticmethod
    def _extract_names_from_text(raw_text: str) -> List[str]:
        """Extract possible company names from numbered or bulleted text."""
        text = (raw_text or '').strip()
        if not text:
            return []

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        names: List[str] = []

        for line in lines:
            candidate = re.sub(r'^[-*\d\.)\s]+', '', line).strip()
            candidate = re.sub(r'\s*[:\-].*$', '', candidate).strip()
            if len(candidate) < 2:
                continue
            if candidate not in names:
                names.append(candidate)

        return names
    
    def _normalize_insights(self, competitor_name: str, raw_data: Dict[str, Any], insights: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all insight fields are populated."""
        fallback = self._build_fallback_insights(competitor_name, raw_data)
        merged = {**fallback, **(insights or {})}
        merged['customer_sentiment'] = {**fallback['customer_sentiment'], **merged.get('customer_sentiment', {})}
        merged['pricing_strategy'] = {**fallback['pricing_strategy'], **merged.get('pricing_strategy', {})}

        for key in ['key_features', 'messaging_themes', 'market_gaps', 'competitive_threats', 'opportunity_areas']:
            value = merged.get(key)
            if not isinstance(value, list) or not value:
                merged[key] = fallback[key]

        return merged

    def _normalize_recommendations(self, brand_name: str, competitor_data: List[Dict], recommendations: Dict[str, Any], category: str = 'general_b2b') -> Dict[str, Any]:
        """Ensure campaign recommendations always contain useful content."""
        fallback = self._build_fallback_recommendations(brand_name, competitor_data, category)
        merged = {**fallback, **(recommendations or {})}
        merged['messaging_positioning'] = {**fallback['messaging_positioning'], **merged.get('messaging_positioning', {})}
        merged['channel_strategy'] = {**fallback['channel_strategy'], **merged.get('channel_strategy', {})}

        if not isinstance(merged.get('gtm_recommendations'), list) or not merged['gtm_recommendations']:
            merged['gtm_recommendations'] = fallback['gtm_recommendations']

        if not merged.get('overall_strategy'):
            merged['overall_strategy'] = fallback['overall_strategy']

        return merged

    def _normalize_market_analysis(self, brand_name: str, competitors: List[Dict], analysis: Dict[str, Any], category: str = 'general_b2b') -> Dict[str, Any]:
        """Ensure market analysis has clear output for the dashboard."""
        fallback = self._build_fallback_market_analysis(brand_name, competitors, category)
        merged = {**fallback, **(analysis or {})}

        for key in ['key_threats', 'opportunities', 'competitive_advantages', 'vulnerabilities', 'market_trends']:
            value = merged.get(key)
            if not isinstance(value, list) or not value:
                merged[key] = fallback[key]

        if not merged.get('market_position'):
            merged['market_position'] = fallback['market_position']
        if not merged.get('threat_level'):
            merged['threat_level'] = fallback['threat_level']

        return merged

    def _build_fallback_insights(self, competitor_name: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build competitor-specific fallback insights."""
        category = raw_data.get('category', 'general_b2b')
        features = raw_data.get('default_features', [])[:5]
        messaging = raw_data.get('default_messaging', [])[:3]
        weaknesses = raw_data.get('default_weaknesses', [])[:3]
        category_label = self._category_label(category)

        return {
            "key_features": features or [f"Core capabilities in the {category_label} category", "Workflow automation", "Team collaboration"],
            "messaging_themes": messaging or [f"{competitor_name} positions itself as a {category_label} leader", "Efficiency", "Scale"],
            "customer_sentiment": {
                "positives": [f"Users like {competitor_name}'s core feature depth", "Good team adoption", f"Useful {category_label} workflows"],
                "negatives": weaknesses or ["Learning curve", "Pricing complexity"],
                "sentiment_score": 0.68
            },
            "pricing_strategy": {
                "model": "SaaS subscription",
                "tiers": ["Free", "Pro", "Enterprise"],
                "price_range": "Entry-level to enterprise pricing"
            },
            "market_gaps": weaknesses or [f"Advanced {category_label} reporting is limited", "More intuitive onboarding needed"],
            "competitive_threats": [
                f"Feature overlap with {competitor_name}",
                "Aggressive packaging and pricing changes",
                f"Brand trust in the {category_label} category"
            ],
            "opportunity_areas": [
                "Simpler onboarding",
                "Stronger workflow analytics",
                "Sharper value-based positioning"
            ]
        }

    def _build_fallback_recommendations(self, brand_name: str, competitor_data: List[Dict], category: str = 'general_b2b') -> Dict[str, Any]:
        """Build actionable recommendations even if the LLM output is incomplete."""
        top_competitors = [c.get('competitor_name', 'competitor') for c in competitor_data[:3]]
        competitor_line = ", ".join(top_competitors) if top_competitors else "key competitors"
        category_label = self._category_label(category)

        return {
            "messaging_positioning": {
                "headline": f"{brand_name}: the faster way to win in {category_label}",
                "subheadline": f"Show buyers how {brand_name} removes the friction that {competitor_line} still leave behind.",
                "value_props": [
                    f"Faster setup and time-to-value for {category_label} buyers",
                    "Clearer workflows with less clutter",
                    f"Actionable analytics tied to {category_label} outcomes"
                ],
                "differentiation": f"Position {brand_name} as the simpler, more focused alternative in the {category_label} market.",
                "ad_copy": {
                    "email": f"Stop losing time to category sprawl. {brand_name} helps teams move faster from search to execution.",
                    "linkedin": f"Most {category_label} platforms promise everything. {brand_name} wins by making outcomes clearer, faster, and easier to adopt.",
                    "website": f"Replace cluttered workflows with {brand_name}'s focused {category_label} engine."
                }
            },
            "channel_strategy": {
                "primary_channels": ["LinkedIn", "Search", "Review sites"],
                "secondary_channels": ["Email nurture", "Community content"],
                "rationale": f"These channels match where buyers compare {brand_name} against {competitor_line} and seek proof of fit, value, and ROI."
            },
            "gtm_recommendations": [
                {
                    "priority": "High",
                    "title": f"Lead with a clear {category_label} value proposition",
                    "description": f"Make {brand_name}'s homepage and ads focus on fast adoption, lower complexity, and clearer {category_label} outcomes.",
                    "rationale": f"Competitor messaging is crowded with feature claims; this opens space for a cleaner value proposition.",
                    "expected_impact": "Higher click-through and demo conversion from frustrated buyers",
                    "timeline": "1-2 weeks"
                },
                {
                    "priority": "High",
                    "title": "Turn competitor complaints into proof points",
                    "description": f"Use review-driven messages that respond directly to setup friction, pricing anxiety, and weak {category_label} workflows.",
                    "rationale": "Negative review themes create immediate opportunities for differentiated positioning.",
                    "expected_impact": "Improved resonance in paid and outbound campaigns",
                    "timeline": "2-3 weeks"
                },
                {
                    "priority": "Medium",
                    "title": "Publish side-by-side comparison content",
                    "description": f"Create comparison pages showing {brand_name} vs major competitors across onboarding, analytics, and ROI.",
                    "rationale": "Buyers often search for comparisons right before purchase.",
                    "expected_impact": "Better bottom-of-funnel conversion",
                    "timeline": "3-4 weeks"
                }
            ],
            "overall_strategy": f"{brand_name} should position itself as the focused, easier-to-adopt alternative in the {category_label} market, with messaging grounded in clarity, relevance, and measurable ROI."
        }

    def _build_fallback_market_analysis(self, brand_name: str, competitors: List[Dict], category: str = 'general_b2b') -> Dict[str, Any]:
        """Build clear market analysis if the LLM output is missing."""
        top_competitors = [c.get('competitor_name', 'competitor') for c in competitors[:3]]
        competitor_line = ", ".join(top_competitors) if top_competitors else "major competitors"
        category_label = self._category_label(category)

        return {
            "market_position": "Challenger",
            "threat_level": "High",
            "key_threats": [
                f"{competitor_line} dominate mindshare with broader ecosystems in the {category_label} market",
                f"Buyer confusion from similar claims across the {category_label} category",
                "Pricing pressure from lower-cost and freemium alternatives"
            ],
            "opportunities": [
                f"Differentiate {brand_name} with cleaner {category_label} design",
                "Own the easiest-to-adopt story",
                "Use customer complaints as proof points in messaging"
            ],
            "competitive_advantages": [
                "Focused product story",
                "Simpler positioning",
                "Faster activation potential"
            ],
            "vulnerabilities": [
                "Need to prove depth without adding clutter",
                "Need stronger comparison content",
                "Need visible ROI narrative"
            ],
            "market_trends": [
                f"AI-enhanced {category_label} workflows",
                "Demand for cleaner tool consolidation",
                "More scrutiny on onboarding and time-to-value"
            ]
        }

    @staticmethod
    def _category_label(category: str) -> str:
        labels = {
            'productivity': 'productivity',
            'ecommerce': 'ecommerce',
            'sportswear': 'sportswear',
            'electronics': 'consumer electronics',
            'beverages': 'beverages',
            'general_b2b': 'B2B software'
        }
        return labels.get(category, 'B2B software')

    @staticmethod
    def _default_insights() -> Dict:
        """Legacy default insights template kept for compatibility."""
        return {
            "key_features": ["Workflow automation", "Collaboration", "Reporting"],
            "messaging_themes": ["Productivity", "Collaboration", "Scale"],
            "customer_sentiment": {
                "positives": ["Easy to use", "Good support", "Fast setup"],
                "negatives": ["Learning curve", "Pricing", "Too many features"],
                "sentiment_score": 0.72
            },
            "pricing_strategy": {
                "model": "SaaS subscription",
                "tiers": ["Free", "Pro", "Enterprise"],
                "price_range": "From free to enterprise tiers"
            },
            "market_gaps": ["Mobile experience", "Advanced analytics", "Onboarding clarity"],
            "competitive_threats": ["Feature parity", "Price competition", "Category clutter"],
            "opportunity_areas": ["Vertical integration", "APIs", "Fast time-to-value"]
        }
    
    @staticmethod
    def _default_recommendations() -> Dict:
        """Legacy default recommendations template kept for compatibility."""
        return {
            "messaging_positioning": {
                "headline": "Lead with clarity, speed, and measurable ROI",
                "subheadline": "Show buyers the faster path from project clutter to execution clarity.",
                "value_props": ["Fast onboarding", "Clear workflows", "Proof of ROI"],
                "differentiation": "Position the product as the focused alternative to cluttered all-in-one suites.",
                "ad_copy": {
                    "email": "Cut the clutter. Get teams aligned faster with a product built for clarity and speed.",
                    "linkedin": "When competitors add more features, you need more focus. Lead with simpler execution.",
                    "website": "Replace work sprawl with a clearer path to outcomes."
                }
            },
            "channel_strategy": {
                "primary_channels": ["LinkedIn", "Search", "Review sites"],
                "secondary_channels": ["Email nurture", "Community"],
                "rationale": "Buyers actively compare vendors in these channels before purchase."
            },
            "gtm_recommendations": [
                {
                    "priority": "High",
                    "title": "Message around simplicity",
                    "description": "Create homepage and paid media copy that clearly explains how the product reduces friction.",
                    "rationale": "This is the most defensible position against crowded category claims.",
                    "expected_impact": "Higher conversion from confused buyers",
                    "timeline": "1-2 weeks"
                }
            ],
            "overall_strategy": "Lead with clarity, speed, and ROI so the product feels easier and more trustworthy than crowded all-in-one competitors."
        }
