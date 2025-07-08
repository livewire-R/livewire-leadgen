import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

# Import all models to ensure they're registered
from src.models.user import db as user_db
from src.models.lead import db as lead_db
from src.models.auth import db as auth_db, create_admin_user, Client
from src.models.campaign import db as campaign_db

# Import routes
from src.routes.user import user_bp
from src.routes.automation import automation_bp
from src.routes.auth import auth_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'leadai-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable CORS for all routes with credentials support
CORS(app, origins="*", supports_credentials=True)

# Initialize database with all models
auth_db.init_app(app)
user_db.init_app(app)
lead_db.init_app(app)
campaign_db.init_app(app)

# Use auth_db as the main database instance
db = auth_db

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(automation_bp, url_prefix='/api/automation')
app.register_blueprint(auth_bp, url_prefix='/api/auth')

# Create all database tables and initialize data
with app.app_context():
    db.create_all()
    
    # Create default admin user if none exists
    admin_exists = Client.query.filter_by(is_admin=True).first()
    if not admin_exists:
        create_admin_user()
        print("✅ Created default admin user: admin / admin123")
        print("🔗 Login at: http://localhost:5000/login")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve static files and SPA routing"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'LeadAI Automation Backend',
        'version': '2.0.0',
        'features': ['authentication', 'linkedin_integration', 'multi_client']
    })

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        'success': True,
        'service': 'LeadAI Automation API',
        'version': '2.0.0',
        'endpoints': {
            'authentication': '/api/auth/*',
            'automation': '/api/automation/*',
            'users': '/api/users/*'
        },
        'features': {
            'client_authentication': True,
            'linkedin_integration': True,
            'apollo_integration': True,
            'hunter_integration': True,
            'campaign_management': True,
            'admin_panel': True
        }
    })

if __name__ == '__main__':
    print("🚀 Starting LeadAI Automation Backend...")
    print("📊 Dashboard: http://localhost:5000")
    print("🔐 Admin Login: admin / admin123")
    print("📖 API Docs: http://localhost:5000/api/status")
    app.run(host='0.0.0.0', port=5000, debug=True)

