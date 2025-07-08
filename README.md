# 🚀 LiveWire Data Solutions - Lead Generation Platform

[![Deploy to AWS](https://github.com/your-username/livewire-leadgen/actions/workflows/deploy-aws.yml/badge.svg)](https://github.com/your-username/livewire-leadgen/actions/workflows/deploy-aws.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

> **Professional AI-powered lead generation platform for Australian B2B consultants**

## 🎯 **Overview**

LiveWire Data Solutions is a comprehensive, multi-client lead generation platform that automates the discovery, scoring, and management of high-quality B2B leads. Built specifically for Australian consultants and service providers.

### **Key Features**
- 🤖 **Automated Lead Generation** via Apollo.io, Hunter.io, and LinkedIn APIs
- 🔐 **Multi-Client Architecture** with complete data isolation
- 📊 **AI-Powered Lead Scoring** (0-100 quality scoring system)
- 🇦🇺 **Australian B2B Focus** with local compliance and data residency
- ⚡ **Serverless AWS Infrastructure** for unlimited scalability
- 👑 **Admin Management System** for client and system control

## 🚀 **Quick Deploy to AWS**

### **One-Click Deployment**
1. **Fork this repository**
2. **Add AWS credentials** to GitHub Secrets
3. **Click "Deploy"** in GitHub Actions
4. **Access your platform** in 5 minutes!

### **GitHub Secrets Required**
```
AWS_ACCESS_KEY_ID: Your AWS access key
AWS_SECRET_ACCESS_KEY: Your AWS secret key
```

### **Deploy Button**
[![Deploy to AWS](https://img.shields.io/badge/Deploy%20to%20AWS-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)](../../actions/workflows/deploy-aws.yml)

## 📋 **Prerequisites**

- **AWS Account** with billing enabled
- **GitHub Account** for repository and deployment
- **API Keys** (optional, configured per client):
  - Apollo.io API key
  - Hunter.io API key
  - LinkedIn Developer App

## 🛠️ **Local Development**

### **Setup**
```bash
# Clone repository
git clone https://github.com/your-username/livewire-leadgen.git
cd livewire-leadgen

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run locally
cd src
python main.py
```

### **Local Testing**
```bash
# Access local application
http://localhost:5000

# Default admin login
Username: admin
Password: admin123
```

## 🌐 **AWS Deployment**

### **Automated Deployment (Recommended)**

**Via GitHub Actions:**
1. **Push to main branch** → Automatic deployment
2. **Manual deployment** → Go to Actions → "Deploy LiveWire to AWS"
3. **Choose environment** → Production or Staging
4. **Select region** → Australia (ap-southeast-2) recommended

### **Manual Deployment**
```bash
# Navigate to deployment directory
cd aws-deployment

# Install dependencies
npm install
pip install -r requirements-aws.txt

# Deploy to AWS
./deploy.sh prod ap-southeast-2
```

### **Deployment Outputs**
```
🎉 Deployment completed successfully!

📋 Your LiveWire Application Details:
🔗 Application URL: https://abc123.execute-api.ap-southeast-2.amazonaws.com/prod
🔐 Admin Login: admin / admin123
📊 Health Check: https://abc123.execute-api.ap-southeast-2.amazonaws.com/prod/health
```

## 🏗️ **Architecture**

### **AWS Services Used**
- **AWS Lambda** - Serverless application hosting
- **Amazon DynamoDB** - NoSQL database for leads and clients
- **Amazon S3** - File storage and static assets
- **API Gateway** - REST API endpoints
- **CloudWatch** - Monitoring and logging
- **IAM** - Security and access control

### **Security Features**
- 🔐 **Client Data Isolation** - Database-level security
- 🔑 **JWT Authentication** - Secure session management
- 🛡️ **Encryption at Rest** - All data encrypted
- 🌏 **Australian Data Residency** - Compliance ready
- 📝 **Audit Logging** - Complete activity tracking

## 👥 **Multi-Client Management**

### **Admin Features**
- **Client Account Creation** - Full credential control
- **Usage Monitoring** - Track lead generation per client
- **Billing Management** - Set limits and pricing tiers
- **Security Controls** - Suspend/activate accounts
- **System Analytics** - Performance and cost tracking

### **Client Features**
- **Personal Dashboard** - Lead management interface
- **API Configuration** - Own Apollo.io, Hunter.io, LinkedIn keys
- **Campaign Management** - Automated lead generation workflows
- **Lead Export** - CSV/Excel export for CRM integration
- **Usage Analytics** - Personal performance metrics

## 💰 **Cost Structure**

### **AWS Infrastructure Costs**
- **Small (1-5 clients):** $19-55 AUD/month
- **Medium (5-20 clients):** $55-160 AUD/month
- **Large (20+ clients):** $160-420 AUD/month

### **Revenue Model**
- **Charge clients:** $199-499 AUD/month per client
- **Your costs:** $19-55 AUD/month total infrastructure
- **Profit margin:** 85-95% after API costs
- **Scalability:** Unlimited clients on same infrastructure

## 🔧 **Configuration**

### **Environment Variables**
```bash
# AWS Configuration
AWS_REGION=ap-southeast-2
ENVIRONMENT=prod

# Application Settings
SECRET_KEY=your-secret-key
DATABASE_URL=dynamodb://livewire-prod-clients

# API Settings (per client)
APOLLO_API_KEY=client-specific-key
HUNTER_API_KEY=client-specific-key
LINKEDIN_CLIENT_ID=client-specific-id
```

### **Client Onboarding**
1. **Admin creates client account**
2. **Client receives login credentials**
3. **Client configures API keys**
4. **Client starts generating leads**
5. **Admin monitors usage and billing**

## 📊 **API Documentation**

### **Authentication Endpoints**
```bash
POST /api/auth/login          # Client login
POST /api/auth/logout         # Client logout
GET  /api/auth/profile        # Get client profile
POST /api/auth/admin/clients  # Create client (admin only)
```

### **Lead Generation Endpoints**
```bash
POST /api/automation/generate-leads    # Generate leads
GET  /api/automation/leads             # Get client leads
POST /api/automation/linkedin/search   # LinkedIn search
GET  /api/automation/campaigns         # Get campaigns
```

### **Admin Endpoints**
```bash
GET  /api/admin/clients        # List all clients
GET  /api/admin/usage          # Usage analytics
GET  /api/admin/costs          # Cost breakdown
POST /api/admin/reset-password # Reset client password
```

## 🔍 **Monitoring & Analytics**

### **CloudWatch Dashboards**
- **Application Performance** - Response times, error rates
- **Lead Generation Metrics** - Success rates, API usage
- **Cost Tracking** - Per-client cost attribution
- **Security Monitoring** - Failed logins, suspicious activity

### **Key Metrics**
- **Lead Generation Rate** - Leads per hour/day
- **Lead Quality Score** - Average scoring across clients
- **API Success Rate** - Apollo.io, Hunter.io, LinkedIn performance
- **Client Engagement** - Login frequency, feature usage

## 🛡️ **Security & Compliance**

### **Data Protection**
- **Encryption at Rest** - All DynamoDB tables encrypted
- **Encryption in Transit** - HTTPS/TLS for all communications
- **Access Controls** - IAM roles with least privilege
- **Data Isolation** - Client data completely separated

### **Compliance Features**
- **GDPR Compliance** - Data export and deletion capabilities
- **Privacy Act (Australia)** - Local data residency options
- **SOC 2** - Audit logging and access controls
- **Data Retention** - Configurable retention policies

## 🚨 **Troubleshooting**

### **Common Issues**

**Deployment Fails:**
```bash
# Check AWS credentials
aws sts get-caller-identity

# View deployment logs
serverless logs -f app --stage prod
```

**Client Can't Login:**
```bash
# Check DynamoDB client table
aws dynamodb scan --table-name livewire-prod-clients

# Reset client password (admin)
curl -X POST https://your-api-url/api/auth/admin/reset-password
```

**API Keys Not Working:**
```bash
# Test client API configuration
curl -X POST https://your-api-url/api/automation/test-apis
```

## 📈 **Scaling & Performance**

### **Auto-Scaling Features**
- **Lambda Concurrency** - Automatic scaling based on demand
- **DynamoDB Auto-Scaling** - Read/write capacity adjustment
- **API Gateway Throttling** - Rate limiting and burst control
- **CloudFront CDN** - Global content delivery

### **Performance Optimization**
- **Database Indexing** - Optimized queries for fast response
- **Caching Strategy** - Redis for frequently accessed data
- **Connection Pooling** - Efficient database connections
- **Async Processing** - Background lead generation jobs

## 🤝 **Contributing**

### **Development Workflow**
1. **Fork the repository**
2. **Create feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit changes** (`git commit -m 'Add amazing feature'`)
4. **Push to branch** (`git push origin feature/amazing-feature`)
5. **Open Pull Request**

### **Code Standards**
- **Python:** PEP 8 compliance
- **JavaScript:** ESLint configuration
- **Documentation:** Comprehensive docstrings
- **Testing:** Unit tests for all functions

## 📞 **Support**

### **Documentation**
- **[Deployment Guide](AWS_DEPLOYMENT_COMPLETE_GUIDE.md)** - Complete AWS setup
- **[Admin Guide](ADMIN_MANAGEMENT_GUIDE.md)** - Client management
- **[Client Guide](CLIENT_ONBOARDING_GUIDE.md)** - User documentation

### **Getting Help**
- **Issues:** [GitHub Issues](../../issues)
- **Discussions:** [GitHub Discussions](../../discussions)
- **Email:** support@livewiredata.com.au

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **Apollo.io** - Lead generation API
- **Hunter.io** - Email verification service
- **AWS** - Cloud infrastructure
- **Serverless Framework** - Deployment automation

---

**Built with ❤️ by LiveWire Data Solutions for Australian B2B consultants**

[![LiveWire Data Solutions](https://img.shields.io/badge/LiveWire-Data%20Solutions-blue?style=for-the-badge)](https://livewiredata.com.au)

