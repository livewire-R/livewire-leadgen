from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets
import json

db = SQLAlchemy()

class Client(db.Model):
    """Client model for admin-controlled user accounts"""
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic Information
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Client Details
    company_name = db.Column(db.String(200))
    contact_name = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    
    # Account Status
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Subscription & Limits
    subscription_plan = db.Column(db.String(50), default='basic')  # basic, pro, enterprise
    monthly_lead_limit = db.Column(db.Integer, default=500)
    leads_used_this_month = db.Column(db.Integer, default=0)
    
    # API Configurations
    apollo_api_key = db.Column(db.String(500))  # Client's own Apollo key
    hunter_api_key = db.Column(db.String(500))  # Client's own Hunter key
    linkedin_access_token = db.Column(db.Text)  # LinkedIn OAuth token
    linkedin_refresh_token = db.Column(db.Text)  # LinkedIn refresh token
    linkedin_token_expires = db.Column(db.DateTime)
    
    # LinkedIn API Configuration
    linkedin_client_id = db.Column(db.String(200))
    linkedin_client_secret = db.Column(db.String(500))
    
    # Usage Tracking
    last_login = db.Column(db.DateTime)
    last_lead_generation = db.Column(db.DateTime)
    total_leads_generated = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = db.relationship('ClientSession', backref='client', lazy=True, cascade='all, delete-orphan')
    leads = db.relationship('Lead', backref='client', lazy=True)
    campaigns = db.relationship('LeadCampaign', backref='client', lazy=True)
    
    def __repr__(self):
        return f'<Client {self.username}>'
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_sensitive=False):
        """Convert client to dictionary for JSON serialization"""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'company_name': self.company_name,
            'contact_name': self.contact_name,
            'phone': self.phone,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'subscription_plan': self.subscription_plan,
            'monthly_lead_limit': self.monthly_lead_limit,
            'leads_used_this_month': self.leads_used_this_month,
            'total_leads_generated': self.total_leads_generated,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'last_lead_generation': self.last_lead_generation.isoformat() if self.last_lead_generation else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'has_apollo_key': bool(self.apollo_api_key),
            'has_hunter_key': bool(self.hunter_api_key),
            'has_linkedin_token': bool(self.linkedin_access_token),
            'linkedin_token_valid': self.is_linkedin_token_valid()
        }
        
        if include_sensitive:
            data.update({
                'apollo_api_key': self.apollo_api_key,
                'hunter_api_key': self.hunter_api_key,
                'linkedin_client_id': self.linkedin_client_id,
                'linkedin_client_secret': self.linkedin_client_secret
            })
        
        return data
    
    def is_linkedin_token_valid(self):
        """Check if LinkedIn token is valid and not expired"""
        if not self.linkedin_access_token:
            return False
        
        if self.linkedin_token_expires and self.linkedin_token_expires < datetime.utcnow():
            return False
        
        return True
    
    def can_generate_leads(self, count=1):
        """Check if client can generate more leads this month"""
        if not self.is_active:
            return False, "Account is inactive"
        
        if self.leads_used_this_month + count > self.monthly_lead_limit:
            return False, f"Monthly limit exceeded ({self.leads_used_this_month}/{self.monthly_lead_limit})"
        
        return True, "OK"
    
    def increment_lead_usage(self, count=1):
        """Increment lead usage counter"""
        self.leads_used_this_month += count
        self.total_leads_generated += count
        self.last_lead_generation = datetime.utcnow()
        db.session.commit()
    
    def reset_monthly_usage(self):
        """Reset monthly usage counter (called by admin or cron job)"""
        self.leads_used_this_month = 0
        db.session.commit()
    
    @classmethod
    def create_client(cls, username, email, password, company_name=None, contact_name=None, 
                     subscription_plan='basic', monthly_lead_limit=500, is_admin=False):
        """Create a new client account"""
        client = cls(
            username=username,
            email=email,
            company_name=company_name,
            contact_name=contact_name,
            subscription_plan=subscription_plan,
            monthly_lead_limit=monthly_lead_limit,
            is_admin=is_admin
        )
        client.set_password(password)
        
        db.session.add(client)
        db.session.commit()
        
        return client


class ClientSession(db.Model):
    """Client session management for secure login"""
    __tablename__ = 'client_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    
    # Session Data
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.Text)
    
    # Session Status
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ClientSession {self.session_token[:8]}...>'
    
    @classmethod
    def create_session(cls, client_id, ip_address=None, user_agent=None, duration_hours=24):
        """Create a new client session"""
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
        
        session = cls(
            client_id=client_id,
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )
        
        db.session.add(session)
        db.session.commit()
        
        return session
    
    def is_valid(self):
        """Check if session is valid and not expired"""
        return (
            self.is_active and 
            self.expires_at > datetime.utcnow()
        )
    
    def extend_session(self, hours=24):
        """Extend session expiration"""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.last_activity = datetime.utcnow()
        db.session.commit()
    
    def invalidate(self):
        """Invalidate the session"""
        self.is_active = False
        db.session.commit()
    
    @classmethod
    def cleanup_expired_sessions(cls):
        """Remove expired sessions (called by cron job)"""
        expired_sessions = cls.query.filter(
            cls.expires_at < datetime.utcnow()
        ).all()
        
        for session in expired_sessions:
            db.session.delete(session)
        
        db.session.commit()
        return len(expired_sessions)


class LinkedInIntegration(db.Model):
    """LinkedIn API integration settings per client"""
    __tablename__ = 'linkedin_integrations'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    
    # LinkedIn App Configuration
    app_name = db.Column(db.String(200))
    client_id_linkedin = db.Column(db.String(200))
    client_secret = db.Column(db.String(500))
    
    # OAuth Tokens
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    token_expires_at = db.Column(db.DateTime)
    
    # API Usage Tracking
    daily_api_calls = db.Column(db.Integer, default=0)
    monthly_api_calls = db.Column(db.Integer, default=0)
    last_api_call = db.Column(db.DateTime)
    
    # Rate Limiting
    calls_per_day_limit = db.Column(db.Integer, default=100)
    calls_per_month_limit = db.Column(db.Integer, default=3000)
    
    # Search Preferences
    default_search_location = db.Column(db.String(100), default='Australia')
    default_industries = db.Column(db.Text)  # JSON array
    default_company_sizes = db.Column(db.Text)  # JSON array
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    last_sync = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    client = db.relationship('Client', backref='linkedin_integration', uselist=False)
    
    def __repr__(self):
        return f'<LinkedInIntegration {self.client_id}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'app_name': self.app_name,
            'has_credentials': bool(self.client_id_linkedin and self.client_secret),
            'has_access_token': bool(self.access_token),
            'token_valid': self.is_token_valid(),
            'daily_api_calls': self.daily_api_calls,
            'monthly_api_calls': self.monthly_api_calls,
            'calls_per_day_limit': self.calls_per_day_limit,
            'calls_per_month_limit': self.calls_per_month_limit,
            'default_search_location': self.default_search_location,
            'default_industries': json.loads(self.default_industries) if self.default_industries else [],
            'default_company_sizes': json.loads(self.default_company_sizes) if self.default_company_sizes else [],
            'is_active': self.is_active,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def is_token_valid(self):
        """Check if access token is valid and not expired"""
        if not self.access_token:
            return False
        
        if self.token_expires_at and self.token_expires_at < datetime.utcnow():
            return False
        
        return True
    
    def can_make_api_call(self):
        """Check if client can make LinkedIn API calls"""
        if not self.is_active or not self.is_token_valid():
            return False, "LinkedIn integration not active or token invalid"
        
        if self.daily_api_calls >= self.calls_per_day_limit:
            return False, f"Daily API limit reached ({self.daily_api_calls}/{self.calls_per_day_limit})"
        
        if self.monthly_api_calls >= self.calls_per_month_limit:
            return False, f"Monthly API limit reached ({self.monthly_api_calls}/{self.calls_per_month_limit})"
        
        return True, "OK"
    
    def increment_api_usage(self):
        """Increment API usage counters"""
        self.daily_api_calls += 1
        self.monthly_api_calls += 1
        self.last_api_call = datetime.utcnow()
        db.session.commit()
    
    def reset_daily_usage(self):
        """Reset daily API usage counter"""
        self.daily_api_calls = 0
        db.session.commit()
    
    def reset_monthly_usage(self):
        """Reset monthly API usage counter"""
        self.monthly_api_calls = 0
        db.session.commit()


class AdminSettings(db.Model):
    """Global admin settings for the platform"""
    __tablename__ = 'admin_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Platform Settings
    platform_name = db.Column(db.String(200), default='LeadAI Pro')
    platform_description = db.Column(db.Text)
    
    # Default Limits
    default_monthly_lead_limit = db.Column(db.Integer, default=500)
    default_session_duration_hours = db.Column(db.Integer, default=24)
    
    # API Rate Limits
    apollo_rate_limit_per_second = db.Column(db.Float, default=1.0)
    hunter_rate_limit_per_second = db.Column(db.Float, default=1.0)
    linkedin_rate_limit_per_day = db.Column(db.Integer, default=100)
    
    # Security Settings
    require_strong_passwords = db.Column(db.Boolean, default=True)
    max_login_attempts = db.Column(db.Integer, default=5)
    lockout_duration_minutes = db.Column(db.Integer, default=30)
    
    # Email Settings
    smtp_server = db.Column(db.String(200))
    smtp_port = db.Column(db.Integer, default=587)
    smtp_username = db.Column(db.String(200))
    smtp_password = db.Column(db.String(500))
    from_email = db.Column(db.String(200))
    
    # Backup Settings
    auto_backup_enabled = db.Column(db.Boolean, default=True)
    backup_frequency_hours = db.Column(db.Integer, default=24)
    backup_retention_days = db.Column(db.Integer, default=30)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<AdminSettings {self.platform_name}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'platform_name': self.platform_name,
            'platform_description': self.platform_description,
            'default_monthly_lead_limit': self.default_monthly_lead_limit,
            'default_session_duration_hours': self.default_session_duration_hours,
            'apollo_rate_limit_per_second': self.apollo_rate_limit_per_second,
            'hunter_rate_limit_per_second': self.hunter_rate_limit_per_second,
            'linkedin_rate_limit_per_day': self.linkedin_rate_limit_per_day,
            'require_strong_passwords': self.require_strong_passwords,
            'max_login_attempts': self.max_login_attempts,
            'lockout_duration_minutes': self.lockout_duration_minutes,
            'auto_backup_enabled': self.auto_backup_enabled,
            'backup_frequency_hours': self.backup_frequency_hours,
            'backup_retention_days': self.backup_retention_days,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def get_settings(cls):
        """Get current admin settings (create default if none exist)"""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings


# Utility functions for authentication
def create_admin_user(username='admin', email='admin@leadai.com', password='admin123'):
    """Create default admin user"""
    admin = Client.query.filter_by(username=username).first()
    if not admin:
        admin = Client.create_client(
            username=username,
            email=email,
            password=password,
            company_name='LeadAI Administration',
            contact_name='System Administrator',
            subscription_plan='enterprise',
            monthly_lead_limit=10000,
            is_admin=True
        )
        print(f"Created admin user: {username}")
    return admin


def authenticate_client(username, password):
    """Authenticate client credentials"""
    client = Client.query.filter_by(username=username).first()
    
    if not client:
        return None, "Invalid username"
    
    if not client.is_active:
        return None, "Account is inactive"
    
    if not client.check_password(password):
        return None, "Invalid password"
    
    # Update last login
    client.last_login = datetime.utcnow()
    db.session.commit()
    
    return client, "Success"


def get_client_by_session_token(session_token):
    """Get client by session token"""
    session = ClientSession.query.filter_by(
        session_token=session_token,
        is_active=True
    ).first()
    
    if not session or not session.is_valid():
        return None
    
    # Update last activity
    session.last_activity = datetime.utcnow()
    db.session.commit()
    
    return session.client

