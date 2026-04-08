"""Database models for KeenFox Intelligence System"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import uuid

db = SQLAlchemy()


class Brand(db.Model):
    """Brand model for storing analyzed brands"""
    __tablename__ = 'brands'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), unique=True, nullable=False, index=True)
    industry = db.Column(db.String(255))
    market_segment = db.Column(db.String(255))
    website = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    competitors = db.relationship('CompetitorAnalysis', backref='brand', lazy=True, cascade='all, delete-orphan')
    reports = db.relationship('IntelligenceReport', backref='brand', lazy=True, cascade='all, delete-orphan')
    campaigns = db.relationship('CampaignRecommendation', backref='brand', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'industry': self.industry,
            'market_segment': self.market_segment,
            'website': self.website,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class CompetitorAnalysis(db.Model):
    """Store analyzed competitors for each brand"""
    __tablename__ = 'competitor_analysis'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    brand_id = db.Column(db.String(36), db.ForeignKey('brands.id'), nullable=False)
    competitor_name = db.Column(db.String(255), nullable=False)
    
    # Analyzed data
    features = db.Column(db.Text)  # JSON string
    messaging = db.Column(db.Text)  # JSON string
    customer_sentiment = db.Column(db.Text)  # JSON string
    pricing = db.Column(db.Text)  # JSON string
    weaknesses = db.Column(db.Text)  # JSON string
    market_position = db.Column(db.String(255))
    threat_level = db.Column(db.String(50))  # 'high', 'medium', 'low'
    
    sources = db.Column(db.Text)  # JSON string of data sources
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_json(self, field_name, data):
        """Helper to set JSON fields"""
        setattr(self, field_name, json.dumps(data) if data else None)
    
    def get_json(self, field_name):
        """Helper to get JSON fields"""
        value = getattr(self, field_name)
        return json.loads(value) if value else None
    
    def to_dict(self):
        return {
            'id': self.id,
            'competitor_name': self.competitor_name,
            'features': self.get_json('features'),
            'messaging': self.get_json('messaging'),
            'customer_sentiment': self.get_json('customer_sentiment'),
            'pricing': self.get_json('pricing'),
            'weaknesses': self.get_json('weaknesses'),
            'market_position': self.market_position,
            'threat_level': self.threat_level,
            'sources': self.get_json('sources'),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class IntelligenceReport(db.Model):
    """Complete intelligence reports"""
    __tablename__ = 'intelligence_reports'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    brand_id = db.Column(db.String(36), db.ForeignKey('brands.id'), nullable=False)
    
    report_title = db.Column(db.String(500))
    report_data = db.Column(db.Text)  # Full JSON report
    summary = db.Column(db.Text)
    key_findings = db.Column(db.Text)  # JSON array
    
    competitors_analyzed = db.Column(db.Integer)  # Count of competitors
    signals_extracted = db.Column(db.Integer)  # Count of signals
    
    file_path = db.Column(db.String(500))  # Path to downloadable report
    file_format = db.Column(db.String(50))  # 'json', 'pdf', 'xlsx'
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'report_title': self.report_title,
            'summary': self.summary,
            'key_findings': json.loads(self.key_findings) if self.key_findings else [],
            'competitors_analyzed': self.competitors_analyzed,
            'signals_extracted': self.signals_extracted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class CampaignRecommendation(db.Model):
    """AI-generated campaign recommendations"""
    __tablename__ = 'campaign_recommendations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    brand_id = db.Column(db.String(36), db.ForeignKey('brands.id'), nullable=False)
    
    # Campaign dimensions
    messaging_copy = db.Column(db.Text)  # JSON with messaging suggestions
    channel_strategy = db.Column(db.Text)  # JSON with channel recommendations
    gtm_recommendations = db.Column(db.Text)  # JSON with 3-5 strategic recommendations
    
    overall_strategy = db.Column(db.Text)  # Synthesized strategy
    priority_score = db.Column(db.Float)  # 0-100 priority ranking
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'messaging_copy': json.loads(self.messaging_copy) if self.messaging_copy else None,
            'channel_strategy': json.loads(self.channel_strategy) if self.channel_strategy else None,
            'gtm_recommendations': json.loads(self.gtm_recommendations) if self.gtm_recommendations else None,
            'overall_strategy': self.overall_strategy,
            'priority_score': self.priority_score,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class WebSignal(db.Model):
    """Store individual web signals extracted from competitors"""
    __tablename__ = 'web_signals'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    competitor_id = db.Column(db.String(36), db.ForeignKey('competitor_analysis.id'), nullable=False)
    
    signal_type = db.Column(db.String(100))  # 'feature', 'pricing', 'review', 'update', etc.
    signal_text = db.Column(db.Text)
    source_url = db.Column(db.String(500))
    sentiment = db.Column(db.String(50))  # 'positive', 'negative', 'neutral'
    relevance_score = db.Column(db.Float)  # 0-1
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'signal_type': self.signal_type,
            'signal_text': self.signal_text,
            'source_url': self.source_url,
            'sentiment': self.sentiment,
            'relevance_score': self.relevance_score,
            'created_at': self.created_at.isoformat()
        }
