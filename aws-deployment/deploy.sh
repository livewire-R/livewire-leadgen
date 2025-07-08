#!/bin/bash

# LeadAI Automation - AWS Deployment Script
# This script deploys the LeadAI automation system to AWS using Serverless Framework

set -e  # Exit on any error

echo "🚀 Starting LeadAI Automation AWS Deployment..."

# Configuration
STAGE=${1:-prod}
REGION=${2:-us-east-1}
SERVICE_NAME="leadai-automation"

echo "📋 Deployment Configuration:"
echo "   Stage: $STAGE"
echo "   Region: $REGION"
echo "   Service: $SERVICE_NAME"
echo ""

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install AWS CLI first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Install Serverless Framework if not installed
echo "📦 Installing Serverless Framework..."
if ! command -v serverless &> /dev/null; then
    npm install -g serverless
    echo "✅ Serverless Framework installed"
else
    echo "✅ Serverless Framework already installed"
fi

# Install Serverless plugins
echo "📦 Installing Serverless plugins..."
npm install --save-dev serverless-wsgi serverless-python-requirements
echo "✅ Serverless plugins installed"

# Create Python virtual environment
echo "🐍 Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate
echo "✅ Virtual environment activated"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements-aws.txt
echo "✅ Python dependencies installed"

# Copy source files to deployment directory
echo "📁 Preparing deployment files..."
cp -r ../src ./ 2>/dev/null || true
cp ../requirements.txt ./ 2>/dev/null || true

# Set environment variables for deployment
export SECRET_KEY=${SECRET_KEY:-$(openssl rand -base64 32)}
export DATABASE_URL=${DATABASE_URL:-"sqlite:///tmp/app.db"}

echo "🔐 Environment variables configured"

# Validate serverless configuration
echo "🔍 Validating Serverless configuration..."
serverless print --stage $STAGE --region $REGION > /dev/null
echo "✅ Serverless configuration valid"

# Deploy to AWS
echo "🚀 Deploying to AWS..."
echo "   This may take several minutes..."
serverless deploy --stage $STAGE --region $REGION --verbose

# Get deployment information
echo ""
echo "📊 Deployment Information:"
serverless info --stage $STAGE --region $REGION

# Test the deployment
echo ""
echo "🧪 Testing deployment..."
ENDPOINT=$(serverless info --stage $STAGE --region $REGION | grep "endpoint:" | awk '{print $2}')

if [ ! -z "$ENDPOINT" ]; then
    echo "🔗 API Endpoint: $ENDPOINT"
    
    # Test health endpoint
    echo "🏥 Testing health endpoint..."
    if curl -s "$ENDPOINT/health" > /dev/null; then
        echo "✅ Health check passed"
    else
        echo "⚠️  Health check failed - service may still be starting"
    fi
    
    # Test API status endpoint
    echo "📡 Testing API status endpoint..."
    if curl -s "$ENDPOINT/api/status" > /dev/null; then
        echo "✅ API status check passed"
    else
        echo "⚠️  API status check failed - service may still be starting"
    fi
else
    echo "⚠️  Could not retrieve endpoint URL"
fi

# Create admin user initialization script
echo ""
echo "👤 Creating admin user initialization..."
cat > init_admin.py << EOF
import requests
import json

# Replace with your actual endpoint
ENDPOINT = "$ENDPOINT"

def init_admin():
    url = f"{ENDPOINT}/api/auth/admin/init"
    
    data = {
        "username": "admin",
        "email": "admin@leadai.com", 
        "password": "admin123"
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print("✅ Admin user created successfully")
            print("🔐 Login credentials:")
            print("   Username: admin")
            print("   Password: admin123")
            print("   URL: $ENDPOINT")
        else:
            print(f"⚠️  Admin user creation response: {response.status_code}")
            print(f"   Message: {response.text}")
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")

if __name__ == "__main__":
    init_admin()
EOF

python init_admin.py

# Cleanup
echo ""
echo "🧹 Cleaning up..."
deactivate 2>/dev/null || true
rm -f init_admin.py

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Next Steps:"
echo "1. 🔗 Access your application: $ENDPOINT"
echo "2. 🔐 Login with admin credentials: admin / admin123"
echo "3. 👥 Create client accounts through the admin panel"
echo "4. 🔑 Configure API keys for each client"
echo "5. 🚀 Start generating leads!"
echo ""
echo "📚 Documentation:"
echo "   - API Documentation: $ENDPOINT/api/status"
echo "   - Health Check: $ENDPOINT/health"
echo ""
echo "🔧 Management Commands:"
echo "   - View logs: serverless logs -f app --stage $STAGE"
echo "   - Remove deployment: serverless remove --stage $STAGE"
echo "   - Update deployment: ./deploy.sh $STAGE $REGION"
echo ""
echo "💡 Remember to:"
echo "   - Change default admin password"
echo "   - Configure custom domain (optional)"
echo "   - Set up monitoring and alerts"
echo "   - Configure backup policies"

