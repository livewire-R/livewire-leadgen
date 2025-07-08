from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Lead(db.Model):
    """Lead model for storing automated lead generation data"""
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Client relationship
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    
    # Basic Information
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))
    
    # Professional Information
    title = db.Column(db.String(200))
    company = db.Column(db.String(200))
    industry = db.Column(db.String(100))
    company_size = db.Column(db.String(50))
    
    # Location
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))
    
    # Lead Scoring and Status
    score = db.Column(db.Integer, default=0)  # 0-100 scoring
    status = db.Column(db.String(20), default='new')  # new, contacted, qualified, converted, lost
    
    # Source and Attribution
    source = db.Column(db.String(100))  # apollo, linkedin, manual, etc.
    source_url = db.Column(db.Text)
    linkedin_url = db.Column(db.Text)
    
    # Enrichment Data
    revenue = db.Column(db.BigInteger)  # Company revenue
    employees = db.Column(db.Integer)  # Number of employees
    technologies = db.Column(db.Text)  # JSON string of technologies used
    
    # Engagement Tracking
    last_contacted = db.Column(db.DateTime)
    contact_attempts = db.Column(db.Integer, default=0)
    email_opened = db.Column(db.Boolean, default=False)
    email_clicked = db.Column(db.Boolean, default=False)
    
    # Notes and Tags
    notes = db.Column(db.Text)
    tags = db.Column(db.Text)  # JSON string of tags
    
    # Automation Flags
    auto_generated = db.Column(db.Boolean, default=True)
    enriched = db.Column(db.Boolean, default=False)
    verified = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Lead {self.first_name} {self.last_name} - {self.company}>'
    
    def to_dict(self):
        """Convert lead to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'title': self.title,
            'company': self.company,
            'industry': self.industry,
            'company_size': self.company_size,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'score': self.score,
            'status': self.status,
            'source': self.source,
            'source_url': self.source_url,
            'linkedin_url': self.linkedin_url,
            'revenue': self.revenue,
            'employees': self.employees,
            'technologies': json.loads(self.technologies) if self.technologies else [],
            'last_contacted': self.last_contacted.isoformat() if self.last_contacted else None,
            'contact_attempts': self.contact_attempts,
            'email_opened': self.email_opened,
            'email_clicked': self.email_clicked,
            'notes': self.notes,
            'tags': json.loads(self.tags) if self.tags else [],
            'auto_generated': self.auto_generated,
            'enriched': self.enriched,
            'verified': self.verified,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_apollo_data(cls, apollo_person):
        """Create Lead from Apollo API response"""
        try:
            # Extract organization data
            org = apollo_person.get('organization', {})
            
            # Calculate lead score based on various factors
            score = cls.calculate_lead_score(apollo_person)
            
            lead = cls(
                first_name=apollo_person.get('first_name', ''),
                last_name=apollo_person.get('last_name', ''),
                email=apollo_person.get('email', ''),
                phone=apollo_person.get('phone_numbers', [{}])[0].get('sanitized_number', '') if apollo_person.get('phone_numbers') else '',
                title=apollo_person.get('title', ''),
                company=org.get('name', ''),
                industry=org.get('industry', ''),
                city=apollo_person.get('city', ''),
                state=apollo_person.get('state', ''),
                country=apollo_person.get('country', ''),
                score=score,
                source='apollo',
                linkedin_url=apollo_person.get('linkedin_url', ''),
                revenue=org.get('estimated_num_employees', 0),
                employees=org.get('estimated_num_employees', 0),
                technologies=json.dumps(org.get('technologies', [])),
                tags=json.dumps(['auto-generated', 'apollo']),
                auto_generated=True
            )
            
            return lead
            
        except Exception as e:
            print(f"Error creating lead from Apollo data: {e}")
            return None
    
    @staticmethod
    def calculate_lead_score(apollo_person):
        """Calculate lead score based on Apollo data"""
        score = 50  # Base score
        
        org = apollo_person.get('organization', {})
        
        # Company size scoring
        employees = org.get('estimated_num_employees', 0)
        if employees > 1000:
            score += 20
        elif employees > 100:
            score += 15
        elif employees > 50:
            score += 10
        elif employees > 10:
            score += 5
        
        # Seniority scoring
        seniority = apollo_person.get('seniority', '').lower()
        if 'c-level' in seniority or 'ceo' in seniority or 'cto' in seniority:
            score += 25
        elif 'director' in seniority or 'vp' in seniority:
            score += 20
        elif 'manager' in seniority:
            score += 15
        elif 'senior' in seniority:
            score += 10
        
        # Industry scoring (Australian B2B focus)
        industry = org.get('industry', '').lower()
        high_value_industries = ['consulting', 'professional services', 'technology', 'finance', 'healthcare']
        if any(ind in industry for ind in high_value_industries):
            score += 15
        
        # Email verification scoring
        if apollo_person.get('email_status') == 'verified':
            score += 10
        
        # LinkedIn presence scoring
        if apollo_person.get('linkedin_url'):
            score += 5
        
        # Ensure score is within bounds
        return min(max(score, 0), 100)


class LeadCampaign(db.Model):
    """Campaign model for organizing lead generation efforts"""
    __tablename__ = 'lead_campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Campaign Configuration
    target_industry = db.Column(db.String(100))
    target_location = db.Column(db.String(100))
    target_company_size = db.Column(db.String(50))
    target_titles = db.Column(db.Text)  # JSON array of job titles
    
    # Campaign Status
    status = db.Column(db.String(20), default='active')  # active, paused, completed
    leads_target = db.Column(db.Integer, default=100)
    leads_generated = db.Column(db.Integer, default=0)
    
    # API Configuration
    api_source = db.Column(db.String(50))  # apollo, linkedin, etc.
    api_config = db.Column(db.Text)  # JSON configuration
    
    # Automation Settings
    auto_enrich = db.Column(db.Boolean, default=True)
    auto_score = db.Column(db.Boolean, default=True)
    auto_contact = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_run = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<LeadCampaign {self.name}>'
    
    def to_dict(self):
        """Convert campaign to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'target_industry': self.target_industry,
            'target_location': self.target_location,
            'target_company_size': self.target_company_size,
            'target_titles': json.loads(self.target_titles) if self.target_titles else [],
            'status': self.status,
            'leads_target': self.leads_target,
            'leads_generated': self.leads_generated,
            'api_source': self.api_source,
            'api_config': json.loads(self.api_config) if self.api_config else {},
            'auto_enrich': self.auto_enrich,
            'auto_score': self.auto_score,
            'auto_contact': self.auto_contact,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_run': self.last_run.isoformat() if self.last_run else None
        }


class LeadSource(db.Model):
    """Track different lead sources and their performance"""
    __tablename__ = 'lead_sources'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    # Performance Metrics
    total_leads = db.Column(db.Integer, default=0)
    qualified_leads = db.Column(db.Integer, default=0)
    converted_leads = db.Column(db.Integer, default=0)
    
    # Cost Tracking
    cost_per_lead = db.Column(db.Float, default=0.0)
    monthly_cost = db.Column(db.Float, default=0.0)
    
    # Configuration
    api_endpoint = db.Column(db.String(500))
    api_key_required = db.Column(db.Boolean, default=True)
    rate_limit = db.Column(db.Integer, default=100)  # requests per hour
    
    # Status
    active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<LeadSource {self.name}>'
    
    def to_dict(self):
        """Convert lead source to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'total_leads': self.total_leads,
            'qualified_leads': self.qualified_leads,
            'converted_leads': self.converted_leads,
            'cost_per_lead': self.cost_per_lead,
            'monthly_cost': self.monthly_cost,
            'conversion_rate': (self.converted_leads / self.total_leads * 100) if self.total_leads > 0 else 0,
            'qualification_rate': (self.qualified_leads / self.total_leads * 100) if self.total_leads > 0 else 0,
            'active': self.active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


    
    def __repr__(self):
        return f'<Lead {self.first_name} {self.last_name} - {self.company}>'
    
    def to_dict(self):
        """Convert lead to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': f"{self.first_name} {self.last_name}",
            'email': self.email,
            'phone': self.phone,
            'title': self.title,
            'company': self.company,
            'industry': self.industry,
            'company_size': self.company_size,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'location': f"{self.city}, {self.state}" if self.city and self.state else (self.city or self.state or ''),
            'score': self.score,
            'status': self.status,
            'source': self.source,
            'source_url': self.source_url,
            'linkedin_url': self.linkedin_url,
            'revenue': self.revenue,
            'employees': self.employees,
            'technologies': json.loads(self.technologies) if self.technologies else [],
            'last_contacted': self.last_contacted.isoformat() if self.last_contacted else None,
            'contact_attempts': self.contact_attempts,
            'email_opened': self.email_opened,
            'email_clicked': self.email_clicked,
            'notes': self.notes,
            'tags': json.loads(self.tags) if self.tags else [],
            'auto_generated': self.auto_generated,
            'enriched': self.enriched,
            'verified': self.verified,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def create_lead(cls, client_id, **kwargs):
        """Create a new lead with client isolation"""
        lead_data = kwargs.copy()
        lead_data['client_id'] = client_id
        
        # Convert lists to JSON strings
        if 'tags' in lead_data and isinstance(lead_data['tags'], list):
            lead_data['tags'] = json.dumps(lead_data['tags'])
        if 'technologies' in lead_data and isinstance(lead_data['technologies'], list):
            lead_data['technologies'] = json.dumps(lead_data['technologies'])
        
        lead = cls(**lead_data)
        return lead
    
    def update_tags(self, tags_list):
        """Update tags from a list"""
        self.tags = json.dumps(tags_list) if tags_list else None
        self.updated_at = datetime.utcnow()
    
    def add_tag(self, tag):
        """Add a single tag"""
        current_tags = json.loads(self.tags) if self.tags else []
        if tag not in current_tags:
            current_tags.append(tag)
            self.tags = json.dumps(current_tags)
            self.updated_at = datetime.utcnow()
    
    def remove_tag(self, tag):
        """Remove a single tag"""
        current_tags = json.loads(self.tags) if self.tags else []
        if tag in current_tags:
            current_tags.remove(tag)
            self.tags = json.dumps(current_tags)
            self.updated_at = datetime.utcnow()
    
    def update_contact_attempt(self):
        """Record a contact attempt"""
        self.contact_attempts += 1
        self.last_contacted = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_email_opened(self):
        """Mark email as opened"""
        self.email_opened = True
        self.updated_at = datetime.utcnow()
    
    def mark_email_clicked(self):
        """Mark email as clicked"""
        self.email_clicked = True
        self.updated_at = datetime.utcnow()


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


class LeadSource(db.Model):
    """Source tracking for lead attribution"""
    __tablename__ = 'lead_sources'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Cost tracking
    cost_per_lead = db.Column(db.Float, default=0.0)
    monthly_cost = db.Column(db.Float, default=0.0)
    
    # Performance metrics
    total_leads = db.Column(db.Integer, default=0)
    conversion_rate = db.Column(db.Float, default=0.0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<LeadSource {self.name}>'

