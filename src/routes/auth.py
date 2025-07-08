import os
import sys
import json
from flask import Blueprint, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
from functools import wraps

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.auth import (
    Client, ClientSession, LinkedInIntegration, AdminSettings,
    authenticate_client, get_client_by_session_token, create_admin_user, db
)
from src.services.linkedin_service import (
    LinkedInService, create_linkedin_oauth_url, exchange_linkedin_code
)

auth_bp = Blueprint('auth', __name__)

# Authentication decorator
def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = request.headers.get('Authorization')
        if session_token and session_token.startswith('Bearer '):
            session_token = session_token[7:]  # Remove 'Bearer ' prefix
        
        if not session_token:
            session_token = request.cookies.get('session_token')
        
        if not session_token:
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'code': 'AUTH_REQUIRED'
            }), 401
        
        client = get_client_by_session_token(session_token)
        if not client:
            return jsonify({
                'success': False,
                'error': 'Invalid or expired session',
                'code': 'INVALID_SESSION'
            }), 401
        
        # Add client to request context
        request.current_client = client
        return f(*args, **kwargs)
    
    return decorated_function

def require_admin(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'current_client') or not request.current_client.is_admin:
            return jsonify({
                'success': False,
                'error': 'Admin privileges required',
                'code': 'ADMIN_REQUIRED'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

@auth_bp.route('/login', methods=['POST'])
def login():
    """Client login endpoint"""
    
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': 'Username and password are required'
            }), 400
        
        username = data['username']
        password = data['password']
        
        # Authenticate client
        client, message = authenticate_client(username, password)
        
        if not client:
            return jsonify({
                'success': False,
                'error': message
            }), 401
        
        # Create session
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        session = ClientSession.create_session(
            client_id=client.id,
            ip_address=ip_address,
            user_agent=user_agent,
            duration_hours=24
        )
        
        # Return session token and client info
        response_data = {
            'success': True,
            'session_token': session.session_token,
            'client': client.to_dict(),
            'expires_at': session.expires_at.isoformat()
        }
        
        response = jsonify(response_data)
        
        # Set session cookie
        response.set_cookie(
            'session_token',
            session.session_token,
            max_age=24*60*60,  # 24 hours
            httponly=True,
            secure=request.is_secure,
            samesite='Lax'
        )
        
        return response
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Client logout endpoint"""
    
    try:
        session_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not session_token:
            session_token = request.cookies.get('session_token')
        
        if session_token:
            session = ClientSession.query.filter_by(session_token=session_token).first()
            if session:
                session.invalidate()
        
        response = jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
        
        # Clear session cookie
        response.set_cookie('session_token', '', expires=0)
        
        return response
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get current client profile"""
    
    try:
        client = request.current_client
        
        return jsonify({
            'success': True,
            'client': client.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile():
    """Update client profile"""
    
    try:
        client = request.current_client
        data = request.get_json()
        
        # Update allowed fields
        if 'company_name' in data:
            client.company_name = data['company_name']
        if 'contact_name' in data:
            client.contact_name = data['contact_name']
        if 'phone' in data:
            client.phone = data['phone']
        if 'email' in data:
            # Check if email is already taken
            existing = Client.query.filter(
                Client.email == data['email'],
                Client.id != client.id
            ).first()
            if existing:
                return jsonify({
                    'success': False,
                    'error': 'Email already in use'
                }), 400
            client.email = data['email']
        
        client.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'client': client.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@require_auth
def change_password():
    """Change client password"""
    
    try:
        client = request.current_client
        data = request.get_json()
        
        if not data or not data.get('current_password') or not data.get('new_password'):
            return jsonify({
                'success': False,
                'error': 'Current password and new password are required'
            }), 400
        
        # Verify current password
        if not client.check_password(data['current_password']):
            return jsonify({
                'success': False,
                'error': 'Current password is incorrect'
            }), 400
        
        # Set new password
        client.set_password(data['new_password'])
        client.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/api-keys', methods=['GET'])
@require_auth
def get_api_keys():
    """Get client's API key configuration"""
    
    try:
        client = request.current_client
        
        return jsonify({
            'success': True,
            'api_keys': {
                'apollo_configured': bool(client.apollo_api_key),
                'hunter_configured': bool(client.hunter_api_key),
                'linkedin_configured': bool(client.linkedin_access_token)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/api-keys', methods=['POST'])
@require_auth
def update_api_keys():
    """Update client's API keys"""
    
    try:
        client = request.current_client
        data = request.get_json()
        
        if 'apollo_api_key' in data:
            client.apollo_api_key = data['apollo_api_key']
        
        if 'hunter_api_key' in data:
            client.hunter_api_key = data['hunter_api_key']
        
        client.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'API keys updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/linkedin/auth-url', methods=['GET'])
@require_auth
def get_linkedin_auth_url():
    """Get LinkedIn OAuth authorization URL"""
    
    try:
        client = request.current_client
        
        # Get or create LinkedIn integration
        linkedin_integration = LinkedInIntegration.query.filter_by(client_id=client.id).first()
        
        if not linkedin_integration or not linkedin_integration.client_id_linkedin:
            return jsonify({
                'success': False,
                'error': 'LinkedIn app credentials not configured. Please contact admin.'
            }), 400
        
        # Generate OAuth URL
        redirect_uri = f"{request.host_url}api/auth/linkedin/callback"
        state = f"client_{client.id}"
        
        auth_url = create_linkedin_oauth_url(
            client_id=linkedin_integration.client_id_linkedin,
            redirect_uri=redirect_uri,
            state=state
        )
        
        return jsonify({
            'success': True,
            'auth_url': auth_url
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/linkedin/callback', methods=['GET'])
def linkedin_callback():
    """Handle LinkedIn OAuth callback"""
    
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            return jsonify({
                'success': False,
                'error': f'LinkedIn authorization failed: {error}'
            }), 400
        
        if not code or not state:
            return jsonify({
                'success': False,
                'error': 'Missing authorization code or state'
            }), 400
        
        # Extract client ID from state
        if not state.startswith('client_'):
            return jsonify({
                'success': False,
                'error': 'Invalid state parameter'
            }), 400
        
        client_id = int(state.replace('client_', ''))
        client = Client.query.get(client_id)
        
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404
        
        # Get LinkedIn integration
        linkedin_integration = LinkedInIntegration.query.filter_by(client_id=client.id).first()
        
        if not linkedin_integration:
            return jsonify({
                'success': False,
                'error': 'LinkedIn integration not configured'
            }), 400
        
        # Exchange code for token
        redirect_uri = f"{request.host_url}api/auth/linkedin/callback"
        
        token_data = exchange_linkedin_code(
            client_id=linkedin_integration.client_id_linkedin,
            client_secret=linkedin_integration.client_secret,
            code=code,
            redirect_uri=redirect_uri
        )
        
        if not token_data:
            return jsonify({
                'success': False,
                'error': 'Failed to exchange code for token'
            }), 400
        
        # Save token data
        linkedin_integration.access_token = token_data.get('access_token')
        linkedin_integration.refresh_token = token_data.get('refresh_token')
        
        # Calculate token expiration
        expires_in = token_data.get('expires_in', 3600)  # Default 1 hour
        linkedin_integration.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        linkedin_integration.is_active = True
        linkedin_integration.last_sync = datetime.utcnow()
        
        db.session.commit()
        
        # Redirect to success page
        return redirect(f"{request.host_url}?linkedin_connected=true")
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/linkedin/status', methods=['GET'])
@require_auth
def get_linkedin_status():
    """Get LinkedIn integration status"""
    
    try:
        client = request.current_client
        
        linkedin_integration = LinkedInIntegration.query.filter_by(client_id=client.id).first()
        
        if not linkedin_integration:
            return jsonify({
                'success': True,
                'linkedin_status': {
                    'configured': False,
                    'connected': False,
                    'token_valid': False
                }
            })
        
        return jsonify({
            'success': True,
            'linkedin_status': {
                'configured': bool(linkedin_integration.client_id_linkedin),
                'connected': bool(linkedin_integration.access_token),
                'token_valid': linkedin_integration.is_token_valid(),
                'daily_calls': linkedin_integration.daily_api_calls,
                'monthly_calls': linkedin_integration.monthly_api_calls,
                'daily_limit': linkedin_integration.calls_per_day_limit,
                'monthly_limit': linkedin_integration.calls_per_month_limit,
                'last_sync': linkedin_integration.last_sync.isoformat() if linkedin_integration.last_sync else None
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/linkedin/disconnect', methods=['POST'])
@require_auth
def disconnect_linkedin():
    """Disconnect LinkedIn integration"""
    
    try:
        client = request.current_client
        
        linkedin_integration = LinkedInIntegration.query.filter_by(client_id=client.id).first()
        
        if linkedin_integration:
            linkedin_integration.access_token = None
            linkedin_integration.refresh_token = None
            linkedin_integration.token_expires_at = None
            linkedin_integration.is_active = False
            
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'LinkedIn disconnected successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Admin routes
@auth_bp.route('/admin/clients', methods=['GET'])
@require_auth
@require_admin
def get_all_clients():
    """Get all clients (admin only)"""
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        clients = Client.query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'clients': [client.to_dict() for client in clients.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': clients.total,
                'pages': clients.pages,
                'has_next': clients.has_next,
                'has_prev': clients.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/admin/clients', methods=['POST'])
@require_auth
@require_admin
def create_client():
    """Create new client (admin only)"""
    
    try:
        data = request.get_json()
        
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'{field} is required'
                }), 400
        
        # Check if username or email already exists
        existing = Client.query.filter(
            (Client.username == data['username']) | 
            (Client.email == data['email'])
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'error': 'Username or email already exists'
            }), 400
        
        # Create client
        client = Client.create_client(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            company_name=data.get('company_name'),
            contact_name=data.get('contact_name'),
            subscription_plan=data.get('subscription_plan', 'basic'),
            monthly_lead_limit=data.get('monthly_lead_limit', 500),
            is_admin=data.get('is_admin', False)
        )
        
        # Create LinkedIn integration if credentials provided
        if data.get('linkedin_client_id') and data.get('linkedin_client_secret'):
            linkedin_integration = LinkedInIntegration(
                client_id=client.id,
                client_id_linkedin=data['linkedin_client_id'],
                client_secret=data['linkedin_client_secret'],
                app_name=data.get('linkedin_app_name', f"{client.username} LinkedIn App")
            )
            db.session.add(linkedin_integration)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'client': client.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/admin/clients/<int:client_id>', methods=['PUT'])
@require_auth
@require_admin
def update_client(client_id):
    """Update client (admin only)"""
    
    try:
        client = Client.query.get(client_id)
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404
        
        data = request.get_json()
        
        # Update fields
        if 'username' in data:
            # Check if username is already taken
            existing = Client.query.filter(
                Client.username == data['username'],
                Client.id != client.id
            ).first()
            if existing:
                return jsonify({
                    'success': False,
                    'error': 'Username already exists'
                }), 400
            client.username = data['username']
        
        if 'email' in data:
            # Check if email is already taken
            existing = Client.query.filter(
                Client.email == data['email'],
                Client.id != client.id
            ).first()
            if existing:
                return jsonify({
                    'success': False,
                    'error': 'Email already exists'
                }), 400
            client.email = data['email']
        
        if 'company_name' in data:
            client.company_name = data['company_name']
        if 'contact_name' in data:
            client.contact_name = data['contact_name']
        if 'phone' in data:
            client.phone = data['phone']
        if 'is_active' in data:
            client.is_active = data['is_active']
        if 'is_admin' in data:
            client.is_admin = data['is_admin']
        if 'subscription_plan' in data:
            client.subscription_plan = data['subscription_plan']
        if 'monthly_lead_limit' in data:
            client.monthly_lead_limit = data['monthly_lead_limit']
        
        # Reset password if provided
        if 'password' in data:
            client.set_password(data['password'])
        
        client.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'client': client.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/admin/clients/<int:client_id>', methods=['DELETE'])
@require_auth
@require_admin
def delete_client(client_id):
    """Delete client (admin only)"""
    
    try:
        client = Client.query.get(client_id)
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404
        
        # Don't allow deleting the last admin
        if client.is_admin:
            admin_count = Client.query.filter_by(is_admin=True).count()
            if admin_count <= 1:
                return jsonify({
                    'success': False,
                    'error': 'Cannot delete the last admin user'
                }), 400
        
        db.session.delete(client)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Client deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/admin/settings', methods=['GET'])
@require_auth
@require_admin
def get_admin_settings():
    """Get admin settings"""
    
    try:
        settings = AdminSettings.get_settings()
        
        return jsonify({
            'success': True,
            'settings': settings.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/admin/settings', methods=['PUT'])
@require_auth
@require_admin
def update_admin_settings():
    """Update admin settings"""
    
    try:
        settings = AdminSettings.get_settings()
        data = request.get_json()
        
        # Update settings
        for key, value in data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        settings.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'settings': settings.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/admin/init', methods=['POST'])
def initialize_admin():
    """Initialize admin user (only works if no admin exists)"""
    
    try:
        # Check if any admin exists
        admin_exists = Client.query.filter_by(is_admin=True).first()
        
        if admin_exists:
            return jsonify({
                'success': False,
                'error': 'Admin user already exists'
            }), 400
        
        data = request.get_json()
        username = data.get('username', 'admin')
        email = data.get('email', 'admin@leadai.com')
        password = data.get('password', 'admin123')
        
        # Create admin user
        admin = create_admin_user(username, email, password)
        
        return jsonify({
            'success': True,
            'message': 'Admin user created successfully',
            'admin': admin.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

