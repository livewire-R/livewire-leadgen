from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class LeadCampaign(db.Model):
    """Campaign model for organizing lead generation efforts per client"""
    __tablename__ = 'lead_campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Client relationship
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    
    # Campaign Details
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Targeting Configuration
    target_industries = db.Column(db.Text)  # JSON array
    target_locations = db.Column(db.Text)  # JSON array
    target_titles = db.Column(db.Text)  # JSON array
    target_company_sizes = db.Column(db.Text)  # JSON array
    target_seniorities = db.Column(db.Text)  # JSON array
    
    # Campaign Goals
    leads_target = db.Column(db.Integer, default=100)
    leads_generated = db.Column(db.Integer, default=0)
    
    # Automation Settings
    auto_run = db.Column(db.Boolean, default=True)
    daily_limit = db.Column(db.Integer, default=25)
    
    # Source Configuration
    use_apollo = db.Column(db.Boolean, default=True)
    use_linkedin = db.Column(db.Boolean, default=False)
    use_hunter = db.Column(db.Boolean, default=True)
    
    # Status and Progress
    status = db.Column(db.String(20), default='active')  # active, paused, completed, cancelled
    progress_percentage = db.Column(db.Float, default=0.0)
    
    # Scheduling
    run_frequency = db.Column(db.String(20), default='daily')  # daily, weekly, manual
    last_run = db.Column(db.DateTime)
    next_run = db.Column(db.DateTime)
    
    # Performance Metrics
    total_api_calls = db.Column(db.Integer, default=0)
    total_cost = db.Column(db.Float, default=0.0)
    average_lead_score = db.Column(db.Float, default=0.0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<LeadCampaign {self.name} - {self.client_id}>'
    
    def to_dict(self):
        """Convert campaign to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'name': self.name,
            'description': self.description,
            'target_industries': json.loads(self.target_industries) if self.target_industries else [],
            'target_locations': json.loads(self.target_locations) if self.target_locations else [],
            'target_titles': json.loads(self.target_titles) if self.target_titles else [],
            'target_company_sizes': json.loads(self.target_company_sizes) if self.target_company_sizes else [],
            'target_seniorities': json.loads(self.target_seniorities) if self.target_seniorities else [],
            'leads_target': self.leads_target,
            'leads_generated': self.leads_generated,
            'auto_run': self.auto_run,
            'daily_limit': self.daily_limit,
            'use_apollo': self.use_apollo,
            'use_linkedin': self.use_linkedin,
            'use_hunter': self.use_hunter,
            'status': self.status,
            'progress_percentage': self.progress_percentage,
            'run_frequency': self.run_frequency,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'total_api_calls': self.total_api_calls,
            'total_cost': self.total_cost,
            'average_lead_score': self.average_lead_score,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def update_progress(self):
        """Update campaign progress percentage"""
        if self.leads_target > 0:
            self.progress_percentage = (self.leads_generated / self.leads_target) * 100
        else:
            self.progress_percentage = 0.0
        
        # Mark as completed if target reached
        if self.leads_generated >= self.leads_target and self.status == 'active':
            self.status = 'completed'
            self.completed_at = datetime.utcnow()
        
        db.session.commit()
    
    def can_run(self):
        """Check if campaign can run"""
        if self.status != 'active':
            return False, f"Campaign status is {self.status}"
        
        if self.leads_generated >= self.leads_target:
            return False, "Campaign target reached"
        
        return True, "OK"
    
    @classmethod
    def create_campaign(cls, client_id, name, description=None, **kwargs):
        """Create a new campaign"""
        campaign = cls(
            client_id=client_id,
            name=name,
            description=description
        )
        
        # Set optional parameters
        for key, value in kwargs.items():
            if hasattr(campaign, key):
                if key in ['target_industries', 'target_locations', 'target_titles', 
                          'target_company_sizes', 'target_seniorities']:
                    # Convert lists to JSON strings
                    setattr(campaign, key, json.dumps(value) if value else None)
                else:
                    setattr(campaign, key, value)
        
        db.session.add(campaign)
        db.session.commit()
        
        return campaign

