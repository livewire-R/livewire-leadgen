"""
Client Data Isolation Middleware

This module ensures that clients can only access their own data
and provides security layers to prevent data leakage between clients.
"""

from functools import wraps
from flask import request, jsonify, g
from sqlalchemy import and_
from src.models.auth import Client, get_client_by_session_token
from src.models.lead import Lead
from src.models.campaign import LeadCampaign


class ClientIsolationError(Exception):
    """Exception raised when client tries to access unauthorized data"""
    pass


def get_current_client():
    """Get the current authenticated client from request context"""
    if hasattr(request, 'current_client'):
        return request.current_client
    
    # Try to get from session token
    session_token = request.headers.get('Authorization')
    if session_token and session_token.startswith('Bearer '):
        session_token = session_token[7:]
    
    if not session_token:
        session_token = request.cookies.get('session_token')
    
    if session_token:
        client = get_client_by_session_token(session_token)
        if client:
            request.current_client = client
            return client
    
    return None


def require_client_isolation(f):
    """
    Decorator to ensure client data isolation
    Automatically filters queries to only include current client's data
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client = get_current_client()
        
        if not client:
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'code': 'AUTH_REQUIRED'
            }), 401
        
        # Store client in Flask's g object for easy access
        g.current_client = client
        g.current_client_id = client.id
        
        return f(*args, **kwargs)
    
    return decorated_function


def ensure_client_owns_resource(resource_client_id, error_message="Access denied"):
    """
    Ensure the current client owns the specified resource
    
    Args:
        resource_client_id: The client_id of the resource being accessed
        error_message: Custom error message
        
    Raises:
        ClientIsolationError: If client doesn't own the resource
    """
    current_client = get_current_client()
    
    if not current_client:
        raise ClientIsolationError("Authentication required")
    
    # Admin users can access all resources
    if current_client.is_admin:
        return True
    
    if current_client.id != resource_client_id:
        raise ClientIsolationError(error_message)
    
    return True


class ClientFilteredQuery:
    """
    Query helper that automatically filters results by client_id
    """
    
    @staticmethod
    def filter_leads_by_client(query, client_id=None):
        """Filter leads query by client ID"""
        if client_id is None:
            client = get_current_client()
            if not client:
                # Return empty query if no client
                return query.filter(Lead.id == -1)
            
            # Admin can see all leads
            if client.is_admin:
                return query
            
            client_id = client.id
        
        return query.filter(Lead.client_id == client_id)
    
    @staticmethod
    def filter_campaigns_by_client(query, client_id=None):
        """Filter campaigns query by client ID"""
        if client_id is None:
            client = get_current_client()
            if not client:
                # Return empty query if no client
                return query.filter(LeadCampaign.id == -1)
            
            # Admin can see all campaigns
            if client.is_admin:
                return query
            
            client_id = client.id
        
        return query.filter(LeadCampaign.client_id == client_id)
    
    @staticmethod
    def get_client_leads(client_id=None, **filters):
        """Get leads for specific client with additional filters"""
        query = Lead.query
        
        # Apply client filter
        query = ClientFilteredQuery.filter_leads_by_client(query, client_id)
        
        # Apply additional filters
        for field, value in filters.items():
            if hasattr(Lead, field) and value is not None:
                query = query.filter(getattr(Lead, field) == value)
        
        return query
    
    @staticmethod
    def get_client_campaigns(client_id=None, **filters):
        """Get campaigns for specific client with additional filters"""
        query = LeadCampaign.query
        
        # Apply client filter
        query = ClientFilteredQuery.filter_campaigns_by_client(query, client_id)
        
        # Apply additional filters
        for field, value in filters.items():
            if hasattr(LeadCampaign, field) and value is not None:
                query = query.filter(getattr(LeadCampaign, field) == value)
        
        return query


def validate_client_access_to_lead(lead_id):
    """
    Validate that current client has access to specific lead
    
    Args:
        lead_id: ID of the lead to check
        
    Returns:
        Lead object if accessible, None otherwise
        
    Raises:
        ClientIsolationError: If access is denied
    """
    client = get_current_client()
    
    if not client:
        raise ClientIsolationError("Authentication required")
    
    lead = Lead.query.get(lead_id)
    
    if not lead:
        return None
    
    # Admin can access all leads
    if client.is_admin:
        return lead
    
    # Check if client owns this lead
    if lead.client_id != client.id:
        raise ClientIsolationError("Access denied: Lead belongs to another client")
    
    return lead


def validate_client_access_to_campaign(campaign_id):
    """
    Validate that current client has access to specific campaign
    
    Args:
        campaign_id: ID of the campaign to check
        
    Returns:
        Campaign object if accessible, None otherwise
        
    Raises:
        ClientIsolationError: If access is denied
    """
    client = get_current_client()
    
    if not client:
        raise ClientIsolationError("Authentication required")
    
    campaign = LeadCampaign.query.get(campaign_id)
    
    if not campaign:
        return None
    
    # Admin can access all campaigns
    if client.is_admin:
        return campaign
    
    # Check if client owns this campaign
    if campaign.client_id != client.id:
        raise ClientIsolationError("Access denied: Campaign belongs to another client")
    
    return campaign


def create_lead_for_client(lead_data, client_id=None):
    """
    Create a new lead ensuring it's assigned to the correct client
    
    Args:
        lead_data: Dictionary of lead data
        client_id: Optional client ID (uses current client if not provided)
        
    Returns:
        Created Lead object
    """
    if client_id is None:
        client = get_current_client()
        if not client:
            raise ClientIsolationError("Authentication required")
        client_id = client.id
    
    # Ensure client_id is set in lead data
    lead_data['client_id'] = client_id
    
    # Create the lead
    lead = Lead(**lead_data)
    
    return lead


def create_campaign_for_client(campaign_data, client_id=None):
    """
    Create a new campaign ensuring it's assigned to the correct client
    
    Args:
        campaign_data: Dictionary of campaign data
        client_id: Optional client ID (uses current client if not provided)
        
    Returns:
        Created Campaign object
    """
    if client_id is None:
        client = get_current_client()
        if not client:
            raise ClientIsolationError("Authentication required")
        client_id = client.id
    
    # Ensure client_id is set in campaign data
    campaign_data['client_id'] = client_id
    
    # Create the campaign
    campaign = LeadCampaign(**campaign_data)
    
    return campaign


class DatabaseSecurityAudit:
    """
    Security audit functions to check for data leakage
    """
    
    @staticmethod
    def audit_lead_access(client_id):
        """
        Audit lead access for a specific client
        Returns statistics about their data access
        """
        client = Client.query.get(client_id)
        if not client:
            return None
        
        # Count leads owned by this client
        owned_leads = Lead.query.filter_by(client_id=client_id).count()
        
        # Count total leads in system (admin only)
        total_leads = Lead.query.count() if client.is_admin else "N/A"
        
        return {
            'client_id': client_id,
            'client_username': client.username,
            'owned_leads': owned_leads,
            'total_leads_in_system': total_leads,
            'is_admin': client.is_admin
        }
    
    @staticmethod
    def audit_campaign_access(client_id):
        """
        Audit campaign access for a specific client
        """
        client = Client.query.get(client_id)
        if not client:
            return None
        
        # Count campaigns owned by this client
        owned_campaigns = LeadCampaign.query.filter_by(client_id=client_id).count()
        
        # Count total campaigns in system (admin only)
        total_campaigns = LeadCampaign.query.count() if client.is_admin else "N/A"
        
        return {
            'client_id': client_id,
            'client_username': client.username,
            'owned_campaigns': owned_campaigns,
            'total_campaigns_in_system': total_campaigns,
            'is_admin': client.is_admin
        }
    
    @staticmethod
    def check_data_isolation():
        """
        Check for potential data isolation issues
        Returns a report of any problems found
        """
        issues = []
        
        # Check for leads without client_id
        orphaned_leads = Lead.query.filter(Lead.client_id.is_(None)).count()
        if orphaned_leads > 0:
            issues.append(f"Found {orphaned_leads} leads without client_id")
        
        # Check for campaigns without client_id
        orphaned_campaigns = LeadCampaign.query.filter(LeadCampaign.client_id.is_(None)).count()
        if orphaned_campaigns > 0:
            issues.append(f"Found {orphaned_campaigns} campaigns without client_id")
        
        # Check for leads assigned to non-existent clients
        invalid_lead_clients = Lead.query.filter(
            ~Lead.client_id.in_(Client.query.with_entities(Client.id))
        ).count()
        if invalid_lead_clients > 0:
            issues.append(f"Found {invalid_lead_clients} leads assigned to non-existent clients")
        
        # Check for campaigns assigned to non-existent clients
        invalid_campaign_clients = LeadCampaign.query.filter(
            ~LeadCampaign.client_id.in_(Client.query.with_entities(Client.id))
        ).count()
        if invalid_campaign_clients > 0:
            issues.append(f"Found {invalid_campaign_clients} campaigns assigned to non-existent clients")
        
        return {
            'issues_found': len(issues),
            'issues': issues,
            'status': 'CLEAN' if len(issues) == 0 else 'ISSUES_FOUND'
        }


# Utility functions for safe data access
def safe_get_lead(lead_id):
    """Safely get a lead ensuring client isolation"""
    try:
        return validate_client_access_to_lead(lead_id)
    except ClientIsolationError:
        return None


def safe_get_campaign(campaign_id):
    """Safely get a campaign ensuring client isolation"""
    try:
        return validate_client_access_to_campaign(campaign_id)
    except ClientIsolationError:
        return None


def safe_get_client_stats():
    """Get statistics for current client only"""
    client = get_current_client()
    if not client:
        return None
    
    if client.is_admin:
        # Admin gets system-wide stats
        return {
            'total_clients': Client.query.count(),
            'total_leads': Lead.query.count(),
            'total_campaigns': LeadCampaign.query.count(),
            'active_clients': Client.query.filter_by(is_active=True).count(),
            'is_admin_view': True
        }
    else:
        # Regular client gets only their stats
        return {
            'my_leads': Lead.query.filter_by(client_id=client.id).count(),
            'my_campaigns': LeadCampaign.query.filter_by(client_id=client.id).count(),
            'my_active_campaigns': LeadCampaign.query.filter_by(
                client_id=client.id, 
                status='active'
            ).count(),
            'is_admin_view': False
        }


# Error handler for client isolation errors
def handle_client_isolation_error(error):
    """Handle ClientIsolationError and return appropriate response"""
    return jsonify({
        'success': False,
        'error': str(error),
        'code': 'ACCESS_DENIED'
    }), 403

