import os
import sys
import json
from flask import Blueprint, request, jsonify
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.lead import Lead, db
from src.models.campaign import LeadCampaign
from src.models.auth import Client
from src.services.apollo_service import ApolloService
from src.services.enrichment_service import EnrichmentService
from src.services.lead_automation import LeadAutomationService
from src.services.linkedin_service import LinkedInService, LinkedInLeadGenService
from src.middleware.client_isolation import (
    require_client_isolation, ClientFilteredQuery, 
    validate_client_access_to_lead, validate_client_access_to_campaign,
    create_lead_for_client, create_campaign_for_client,
    safe_get_client_stats, ClientIsolationError, handle_client_isolation_error
)

automation_bp = Blueprint('automation', __name__)

# Register error handler for client isolation
automation_bp.register_error_handler(ClientIsolationError, handle_client_isolation_error)

@automation_bp.route('/status', methods=['GET'])
@require_client_isolation
def get_automation_status():
    """Get automation status for current client only"""
    try:
        client = request.current_client
        
        # Get client-specific statistics
        stats = safe_get_client_stats()
        
        # Get client's API configuration status
        api_status = {
            'apollo_configured': bool(client.apollo_api_key),
            'hunter_configured': bool(client.hunter_api_key),
            'linkedin_configured': bool(client.linkedin_access_token)
        }
        
        # Get recent activity for this client only
        recent_leads = ClientFilteredQuery.get_client_leads().order_by(
            Lead.created_at.desc()
        ).limit(5).all()
        
        recent_campaigns = ClientFilteredQuery.get_client_campaigns().order_by(
            LeadCampaign.updated_at.desc()
        ).limit(3).all()
        
        return jsonify({
            'success': True,
            'client_id': client.id,
            'client_username': client.username,
            'statistics': stats,
            'api_status': api_status,
            'recent_leads': [lead.to_dict() for lead in recent_leads],
            'recent_campaigns': [campaign.to_dict() for campaign in recent_campaigns],
            'service_status': 'online'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/leads', methods=['GET'])
@require_client_isolation
def get_leads():
    """Get leads for current client only"""
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Filter parameters
        status = request.args.get('status')
        source = request.args.get('source')
        min_score = request.args.get('min_score', type=int)
        
        # Build query with client isolation
        query = ClientFilteredQuery.get_client_leads()
        
        # Apply filters
        if status:
            query = query.filter(Lead.status == status)
        if source:
            query = query.filter(Lead.source == source)
        if min_score:
            query = query.filter(Lead.score >= min_score)
        
        # Order by creation date (newest first)
        query = query.order_by(Lead.created_at.desc())
        
        # Paginate
        leads = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'leads': [lead.to_dict() for lead in leads.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': leads.total,
                'pages': leads.pages,
                'has_next': leads.has_next,
                'has_prev': leads.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/leads/<int:lead_id>', methods=['GET'])
@require_client_isolation
def get_lead(lead_id):
    """Get specific lead (only if owned by current client)"""
    try:
        lead = validate_client_access_to_lead(lead_id)
        
        if not lead:
            return jsonify({
                'success': False,
                'error': 'Lead not found'
            }), 404
        
        return jsonify({
            'success': True,
            'lead': lead.to_dict()
        })
        
    except ClientIsolationError as e:
        return handle_client_isolation_error(e)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/leads/<int:lead_id>', methods=['PUT'])
@require_client_isolation
def update_lead(lead_id):
    """Update specific lead (only if owned by current client)"""
    try:
        lead = validate_client_access_to_lead(lead_id)
        
        if not lead:
            return jsonify({
                'success': False,
                'error': 'Lead not found'
            }), 404
        
        data = request.get_json()
        
        # Update allowed fields
        updatable_fields = [
            'status', 'notes', 'tags', 'score', 'title', 'company',
            'phone', 'city', 'state', 'country'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(lead, field, data[field])
        
        lead.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'lead': lead.to_dict()
        })
        
    except ClientIsolationError as e:
        return handle_client_isolation_error(e)
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/leads/<int:lead_id>', methods=['DELETE'])
@require_client_isolation
def delete_lead(lead_id):
    """Delete specific lead (only if owned by current client)"""
    try:
        lead = validate_client_access_to_lead(lead_id)
        
        if not lead:
            return jsonify({
                'success': False,
                'error': 'Lead not found'
            }), 404
        
        db.session.delete(lead)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Lead deleted successfully'
        })
        
    except ClientIsolationError as e:
        return handle_client_isolation_error(e)
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/campaigns', methods=['GET'])
@require_client_isolation
def get_campaigns():
    """Get campaigns for current client only"""
    try:
        # Get campaigns with client isolation
        campaigns = ClientFilteredQuery.get_client_campaigns().order_by(
            LeadCampaign.created_at.desc()
        ).all()
        
        return jsonify({
            'success': True,
            'campaigns': [campaign.to_dict() for campaign in campaigns]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/campaigns', methods=['POST'])
@require_client_isolation
def create_campaign():
    """Create new campaign for current client"""
    try:
        client = request.current_client
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({
                'success': False,
                'error': 'Campaign name is required'
            }), 400
        
        # Create campaign with client isolation
        campaign_data = {
            'name': data['name'],
            'description': data.get('description'),
            'target_industries': data.get('target_industries', []),
            'target_locations': data.get('target_locations', []),
            'target_titles': data.get('target_titles', []),
            'target_company_sizes': data.get('target_company_sizes', []),
            'target_seniorities': data.get('target_seniorities', []),
            'leads_target': data.get('leads_target', 100),
            'daily_limit': data.get('daily_limit', 25),
            'use_apollo': data.get('use_apollo', True),
            'use_linkedin': data.get('use_linkedin', False),
            'use_hunter': data.get('use_hunter', True)
        }
        
        campaign = create_campaign_for_client(campaign_data, client.id)
        
        db.session.add(campaign)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'campaign': campaign.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/campaigns/<int:campaign_id>', methods=['GET'])
@require_client_isolation
def get_campaign(campaign_id):
    """Get specific campaign (only if owned by current client)"""
    try:
        campaign = validate_client_access_to_campaign(campaign_id)
        
        if not campaign:
            return jsonify({
                'success': False,
                'error': 'Campaign not found'
            }), 404
        
        return jsonify({
            'success': True,
            'campaign': campaign.to_dict()
        })
        
    except ClientIsolationError as e:
        return handle_client_isolation_error(e)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/campaigns/<int:campaign_id>/run', methods=['POST'])
@require_client_isolation
def run_campaign(campaign_id):
    """Run specific campaign (only if owned by current client)"""
    try:
        client = request.current_client
        campaign = validate_client_access_to_campaign(campaign_id)
        
        if not campaign:
            return jsonify({
                'success': False,
                'error': 'Campaign not found'
            }), 404
        
        # Check if client can generate leads
        can_generate, message = client.can_generate_leads(campaign.daily_limit)
        if not can_generate:
            return jsonify({
                'success': False,
                'error': message
            }), 400
        
        # Initialize automation service with client's API keys
        automation_service = LeadAutomationService(
            apollo_api_key=client.apollo_api_key,
            hunter_api_key=client.hunter_api_key
        )
        
        # Run campaign with client isolation
        results = automation_service.run_campaign_for_client(campaign, client.id)
        
        return jsonify({
            'success': True,
            'results': results,
            'campaign': campaign.to_dict()
        })
        
    except ClientIsolationError as e:
        return handle_client_isolation_error(e)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/generate-leads', methods=['POST'])
@require_client_isolation
def generate_leads():
    """Generate leads for current client using their API keys"""
    try:
        client = request.current_client
        data = request.get_json()
        
        # Check if client can generate leads
        lead_count = data.get('count', 25)
        can_generate, message = client.can_generate_leads(lead_count)
        if not can_generate:
            return jsonify({
                'success': False,
                'error': message
            }), 400
        
        # Check API key configuration
        if not client.apollo_api_key:
            return jsonify({
                'success': False,
                'error': 'Apollo API key not configured. Please add your API key in settings.'
            }), 400
        
        # Initialize services with client's API keys
        apollo_service = ApolloService(client.apollo_api_key)
        enrichment_service = EnrichmentService(client.hunter_api_key) if client.hunter_api_key else None
        
        # Generate leads with client isolation
        search_config = data.get('search_config', {
            'person_titles': ['Consultant', 'Director', 'Manager'],
            'person_locations': ['Sydney, AU', 'Melbourne, AU'],
            'organization_industries': ['Corporate Wellness', 'Consulting'],
            'organization_num_employees_ranges': ['11,50', '51,200']
        })
        
        # Search for leads
        apollo_results = apollo_service.search_people(search_config, count=lead_count)
        
        if not apollo_results or not apollo_results.get('people'):
            return jsonify({
                'success': False,
                'error': 'No leads found with current search criteria'
            }), 404
        
        generated_leads = []
        
        for person in apollo_results['people'][:lead_count]:
            # Create lead data with client isolation
            lead_data = {
                'first_name': person.get('first_name', ''),
                'last_name': person.get('last_name', ''),
                'email': person.get('email', ''),
                'title': person.get('title', ''),
                'company': person.get('organization', {}).get('name', ''),
                'industry': person.get('organization', {}).get('industry', ''),
                'city': person.get('city', ''),
                'state': person.get('state', ''),
                'country': person.get('country', ''),
                'source': 'apollo',
                'auto_generated': True,
                'client_id': client.id  # Ensure client isolation
            }
            
            # Enrich with Hunter.io if available
            if enrichment_service and lead_data['email']:
                enrichment_data = enrichment_service.verify_email(lead_data['email'])
                if enrichment_data:
                    lead_data.update(enrichment_data)
                    lead_data['verified'] = True
            
            # Calculate lead score
            lead_data['score'] = calculate_lead_score(lead_data)
            
            # Create lead with client isolation
            lead = create_lead_for_client(lead_data, client.id)
            db.session.add(lead)
            generated_leads.append(lead)
        
        # Update client usage
        client.increment_lead_usage(len(generated_leads))
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'leads_generated': len(generated_leads),
            'leads': [lead.to_dict() for lead in generated_leads],
            'remaining_quota': client.monthly_lead_limit - client.leads_used_this_month
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/linkedin/search', methods=['POST'])
@require_client_isolation
def linkedin_search():
    """Search LinkedIn using client's LinkedIn API credentials"""
    try:
        client = request.current_client
        data = request.get_json()
        
        # Check LinkedIn integration
        if not client.linkedin_access_token:
            return jsonify({
                'success': False,
                'error': 'LinkedIn not connected. Please connect your LinkedIn account first.'
            }), 400
        
        # Check if client can generate leads
        lead_count = data.get('count', 10)
        can_generate, message = client.can_generate_leads(lead_count)
        if not can_generate:
            return jsonify({
                'success': False,
                'error': message
            }), 400
        
        # Initialize LinkedIn service with client's credentials
        linkedin_service = LinkedInService(
            client_id=client.linkedin_client_id,
            client_secret=client.linkedin_client_secret,
            access_token=client.linkedin_access_token
        )
        
        # Validate token
        if not linkedin_service.validate_token():
            return jsonify({
                'success': False,
                'error': 'LinkedIn token expired. Please reconnect your LinkedIn account.'
            }), 400
        
        # Initialize lead generation service
        leadgen_service = LinkedInLeadGenService(linkedin_service)
        
        # Generate leads from LinkedIn with client isolation
        search_keywords = data.get('keywords', ['consulting', 'corporate wellness'])
        location = data.get('location', 'Australia')
        
        linkedin_leads = leadgen_service.generate_leads_from_companies(
            company_keywords=search_keywords,
            location=location,
            max_companies=lead_count
        )
        
        generated_leads = []
        
        for lead_data in linkedin_leads:
            # Ensure client isolation
            lead_data['client_id'] = client.id
            lead_data['source'] = 'linkedin'
            lead_data['auto_generated'] = True
            
            # Calculate score
            lead_data['score'] = calculate_lead_score(lead_data)
            
            # Create lead with client isolation
            lead = create_lead_for_client(lead_data, client.id)
            db.session.add(lead)
            generated_leads.append(lead)
        
        # Update client usage
        client.increment_lead_usage(len(generated_leads))
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'leads_generated': len(generated_leads),
            'leads': [lead.to_dict() for lead in generated_leads],
            'remaining_quota': client.monthly_lead_limit - client.leads_used_this_month
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_bp.route('/test-apis', methods=['POST'])
@require_client_isolation
def test_apis():
    """Test API connections for current client"""
    try:
        client = request.current_client
        results = {}
        
        # Test Apollo API with client's key
        if client.apollo_api_key:
            apollo_service = ApolloService(client.apollo_api_key)
            apollo_test = apollo_service.test_connection()
            results['apollo'] = {
                'configured': True,
                'working': apollo_test,
                'message': 'Connected successfully' if apollo_test else 'Connection failed'
            }
        else:
            results['apollo'] = {
                'configured': False,
                'working': False,
                'message': 'API key not configured'
            }
        
        # Test Hunter API with client's key
        if client.hunter_api_key:
            enrichment_service = EnrichmentService(client.hunter_api_key)
            hunter_test = enrichment_service.test_connection()
            results['hunter'] = {
                'configured': True,
                'working': hunter_test,
                'message': 'Connected successfully' if hunter_test else 'Connection failed'
            }
        else:
            results['hunter'] = {
                'configured': False,
                'working': False,
                'message': 'API key not configured'
            }
        
        # Test LinkedIn API with client's token
        if client.linkedin_access_token:
            linkedin_service = LinkedInService(
                client_id=client.linkedin_client_id or '',
                client_secret=client.linkedin_client_secret or '',
                access_token=client.linkedin_access_token
            )
            linkedin_test = linkedin_service.validate_token()
            results['linkedin'] = {
                'configured': True,
                'working': linkedin_test,
                'message': 'Connected successfully' if linkedin_test else 'Token expired or invalid'
            }
        else:
            results['linkedin'] = {
                'configured': False,
                'working': False,
                'message': 'LinkedIn not connected'
            }
        
        return jsonify({
            'success': True,
            'api_tests': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def calculate_lead_score(lead_data):
    """Calculate lead score based on various factors"""
    score = 50  # Base score
    
    # Company size scoring
    company_size = lead_data.get('company_size', '')
    if '1000+' in company_size or 'Large' in company_size:
        score += 20
    elif '200-1000' in company_size or 'Medium' in company_size:
        score += 15
    elif '50-200' in company_size:
        score += 10
    
    # Title/seniority scoring
    title = lead_data.get('title', '').lower()
    if any(word in title for word in ['ceo', 'cto', 'cfo', 'president']):
        score += 25
    elif any(word in title for word in ['director', 'vp', 'vice president']):
        score += 20
    elif any(word in title for word in ['manager', 'head']):
        score += 15
    elif any(word in title for word in ['senior', 'lead']):
        score += 10
    
    # Industry relevance
    industry = lead_data.get('industry', '').lower()
    if any(word in industry for word in ['consulting', 'professional services', 'wellness']):
        score += 15
    
    # Email verification
    if lead_data.get('verified'):
        score += 10
    
    # LinkedIn profile
    if lead_data.get('linkedin_url'):
        score += 5
    
    return min(score, 100)  # Cap at 100

