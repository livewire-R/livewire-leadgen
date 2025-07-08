# 👑 LeadAI Pro - Admin Management Guide

## 🎯 **Overview**

As the system administrator, you have complete control over all client accounts, system settings, and data management. This guide covers all administrative functions for managing your multi-client LeadAI platform.

## 🔐 **Admin Authentication**

### **Initial Admin Setup**
- **Default Username:** `admin`
- **Default Password:** `admin123`
- **⚠️ CRITICAL:** Change password immediately after first login

### **Admin Login Process**
1. Navigate to your application URL
2. Login with admin credentials
3. Access admin dashboard with full system control

## 👥 **Client Management**

### **Creating New Clients**

**Via Admin Dashboard:**
1. Login as admin
2. Navigate to "Client Management"
3. Click "Add New Client"
4. Fill in required information:
   - Username (unique identifier)
   - Email address
   - Company name
   - Contact person name
   - Monthly lead generation limit
   - Initial password (temporary)
   - Account status (active/inactive)

**Via API (Programmatic):**
```bash
curl -X POST https://your-api-url/api/auth/admin/clients \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{
    "username": "acme_consulting",
    "email": "admin@acmeconsulting.com",
    "password": "TempPass123!",
    "company_name": "ACME Consulting Pty Ltd",
    "contact_name": "Sarah Johnson",
    "monthly_lead_limit": 1000,
    "is_active": true,
    "notes": "Premium client - priority support"
  }'
```

### **Client Account Settings**

**Configurable Parameters:**
- **Monthly Lead Limit:** Control how many leads each client can generate
- **API Access:** Enable/disable specific API integrations
- **Account Status:** Activate or suspend client accounts
- **Billing Tier:** Set pricing tier for different service levels
- **Data Retention:** Configure how long client data is stored

**Example Client Configuration:**
```json
{
  "client_id": "123",
  "username": "acme_consulting",
  "company_name": "ACME Consulting Pty Ltd",
  "contact_name": "Sarah Johnson",
  "email": "admin@acmeconsulting.com",
  "monthly_lead_limit": 1000,
  "leads_used_this_month": 247,
  "is_active": true,
  "is_premium": true,
  "apollo_api_enabled": true,
  "hunter_api_enabled": true,
  "linkedin_api_enabled": true,
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-20T14:22:00Z",
  "billing_tier": "professional",
  "notes": "Premium client - priority support"
}
```

### **Managing Client Credentials**

**Password Management:**
```bash
# Reset client password
curl -X POST https://your-api-url/api/auth/admin/reset-password \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "client_id": "123",
    "new_password": "NewSecurePass123!",
    "force_change_on_login": true
  }'
```

**Account Suspension:**
```bash
# Suspend client account
curl -X PUT https://your-api-url/api/auth/admin/clients/123 \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "is_active": false,
    "suspension_reason": "Payment overdue"
  }'
```

**Account Reactivation:**
```bash
# Reactivate client account
curl -X PUT https://your-api-url/api/auth/admin/clients/123 \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "is_active": true,
    "monthly_lead_limit": 1000
  }'
```

## 📊 **System Monitoring**

### **Dashboard Overview**

**Key Metrics to Monitor:**
- Total active clients
- Total leads generated (all clients)
- System performance metrics
- API usage across all clients
- Monthly costs and revenue
- Error rates and system health

**Admin Dashboard Features:**
- Real-time client activity
- Lead generation statistics
- API usage monitoring
- System performance graphs
- Cost tracking and billing
- Error logs and alerts

### **Client Activity Monitoring**

**View All Client Activity:**
```bash
curl -X GET https://your-api-url/api/admin/activity \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Response Example:**
```json
{
  "success": true,
  "activity": [
    {
      "client_id": "123",
      "client_name": "ACME Consulting",
      "action": "lead_generation",
      "details": "Generated 25 leads via Apollo API",
      "timestamp": "2024-01-20T14:30:00Z",
      "api_cost": 1.25
    },
    {
      "client_id": "456",
      "client_name": "XYZ Corp",
      "action": "linkedin_search",
      "details": "LinkedIn search for 'consulting' keywords",
      "timestamp": "2024-01-20T14:25:00Z",
      "leads_found": 12
    }
  ]
}
```

### **Usage Analytics**

**Monthly Usage Report:**
```bash
curl -X GET https://your-api-url/api/admin/usage/monthly \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "month": "2024-01",
    "include_costs": true
  }'
```

**Client Performance Metrics:**
- Leads generated per client
- API usage and costs
- Login frequency and engagement
- Campaign success rates
- Lead quality scores

## 🔧 **System Configuration**

### **Global Settings**

**API Rate Limits:**
```json
{
  "apollo_requests_per_minute": 60,
  "hunter_requests_per_minute": 100,
  "linkedin_requests_per_hour": 500,
  "max_concurrent_campaigns": 10
}
```

**Default Client Limits:**
```json
{
  "default_monthly_lead_limit": 500,
  "default_daily_lead_limit": 50,
  "default_api_timeout": 30,
  "max_campaign_duration_days": 30
}
```

**System Maintenance:**
```bash
# Enable maintenance mode
curl -X POST https://your-api-url/api/admin/maintenance \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "enabled": true,
    "message": "System maintenance in progress. Back online in 30 minutes.",
    "estimated_duration": 30
  }'
```

### **Data Management**

**Backup Configuration:**
- Automated daily backups of all client data
- Point-in-time recovery for last 30 days
- Cross-region backup replication
- Encrypted backup storage

**Data Retention Policies:**
```json
{
  "leads_retention_days": 365,
  "campaigns_retention_days": 180,
  "logs_retention_days": 90,
  "inactive_client_data_retention_days": 730
}
```

**Data Export (GDPR Compliance):**
```bash
# Export all data for a client
curl -X POST https://your-api-url/api/admin/export-client-data \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "client_id": "123",
    "include_leads": true,
    "include_campaigns": true,
    "include_activity_logs": true,
    "format": "json"
  }'
```

## 💰 **Billing & Cost Management**

### **Cost Tracking**

**Monthly Cost Breakdown:**
```bash
curl -X GET https://your-api-url/api/admin/costs/breakdown \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "month": "2024-01"
  }'
```

**Response:**
```json
{
  "total_cost": 156.78,
  "breakdown": {
    "aws_infrastructure": 45.23,
    "apollo_api_costs": 67.50,
    "hunter_api_costs": 23.45,
    "linkedin_api_costs": 12.30,
    "storage_costs": 8.30
  },
  "cost_per_client": {
    "acme_consulting": 34.56,
    "xyz_corp": 28.90,
    "abc_solutions": 41.23
  }
}
```

### **Billing Management**

**Client Billing Tiers:**
- **Starter:** 500 leads/month - $99/month
- **Professional:** 1,000 leads/month - $199/month
- **Enterprise:** 2,500 leads/month - $399/month
- **Custom:** Unlimited leads - Custom pricing

**Billing API:**
```bash
# Update client billing tier
curl -X PUT https://your-api-url/api/admin/billing/client/123 \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "billing_tier": "professional",
    "monthly_fee": 199.00,
    "lead_limit": 1000,
    "effective_date": "2024-02-01"
  }'
```

## 🚨 **Security & Compliance**

### **Security Monitoring**

**Failed Login Attempts:**
```bash
curl -X GET https://your-api-url/api/admin/security/failed-logins \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Suspicious Activity Detection:**
- Multiple failed login attempts
- Unusual API usage patterns
- Geographic anomalies
- Rapid lead generation spikes

### **Compliance Features**

**GDPR Compliance:**
- Right to data export
- Right to data deletion
- Data processing consent tracking
- Privacy policy enforcement

**Data Deletion (Right to be Forgotten):**
```bash
curl -X DELETE https://your-api-url/api/admin/clients/123/data \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "confirm_deletion": true,
    "retention_override": false,
    "reason": "Client request - GDPR Article 17"
  }'
```

### **Audit Logging**

**All Admin Actions Logged:**
- Client account creation/modification
- Password resets
- Account suspensions
- Data exports/deletions
- System configuration changes
- Billing modifications

**Audit Log Query:**
```bash
curl -X GET https://your-api-url/api/admin/audit-logs \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "action_type": "client_modification"
  }'
```

## 📈 **Performance Optimization**

### **System Performance Monitoring**

**Key Performance Indicators:**
- API response times
- Database query performance
- Lead generation success rates
- System uptime and availability
- Error rates by component

**Performance Alerts:**
- API response time > 2 seconds
- Error rate > 1%
- Database connection issues
- High memory/CPU usage
- Failed lead generation attempts

### **Scaling Recommendations**

**When to Scale Up:**
- More than 50 active clients
- Lead generation > 10,000/month
- API response times increasing
- Database query slowdowns

**Scaling Options:**
- Increase Lambda memory allocation
- Enable DynamoDB auto-scaling
- Add CloudFront CDN
- Implement read replicas
- Multi-region deployment

## 🔧 **Troubleshooting Guide**

### **Common Issues**

**Client Can't Login:**
1. Check account status (active/suspended)
2. Verify password hasn't expired
3. Check for account lockout
4. Review recent security events

**Lead Generation Failing:**
1. Verify client API keys are valid
2. Check API rate limits and quotas
3. Validate search parameters
4. Review error logs for specific issues

**Performance Issues:**
1. Check CloudWatch metrics
2. Review database performance
3. Analyze API response times
4. Monitor memory and CPU usage

### **Emergency Procedures**

**System Outage:**
1. Check AWS service health
2. Review CloudWatch alarms
3. Verify Lambda function status
4. Check DynamoDB table health
5. Escalate to AWS support if needed

**Security Incident:**
1. Immediately suspend affected accounts
2. Review audit logs for breach scope
3. Reset all admin passwords
4. Notify affected clients
5. Document incident for compliance

## 📞 **Support & Maintenance**

### **Regular Maintenance Tasks**

**Daily:**
- Review system health metrics
- Check for failed lead generation jobs
- Monitor API usage and costs
- Review security alerts

**Weekly:**
- Analyze client usage patterns
- Review and respond to support tickets
- Check system performance trends
- Update client billing records

**Monthly:**
- Generate usage and cost reports
- Review and optimize system performance
- Update security configurations
- Plan capacity for growth

### **Client Support Process**

**Support Ticket Categories:**
1. **Login Issues** - Password resets, account lockouts
2. **API Problems** - Configuration, rate limits, errors
3. **Lead Quality** - Scoring issues, data accuracy
4. **Billing Questions** - Usage, costs, plan changes
5. **Feature Requests** - New functionality, integrations

**Support Response Times:**
- **Critical Issues:** 1 hour
- **High Priority:** 4 hours
- **Medium Priority:** 24 hours
- **Low Priority:** 72 hours

## ✅ **Admin Checklist**

### **Daily Tasks**
- [ ] Review system health dashboard
- [ ] Check for client support tickets
- [ ] Monitor API usage and costs
- [ ] Review security alerts

### **Weekly Tasks**
- [ ] Generate client usage reports
- [ ] Review system performance metrics
- [ ] Update client billing records
- [ ] Plan capacity for new clients

### **Monthly Tasks**
- [ ] Generate comprehensive cost reports
- [ ] Review and optimize system performance
- [ ] Update security configurations
- [ ] Plan feature roadmap

### **Quarterly Tasks**
- [ ] Conduct security audit
- [ ] Review disaster recovery procedures
- [ ] Update compliance documentation
- [ ] Plan system upgrades

## 🎉 **Success Metrics**

**System Health:**
- 99.9%+ uptime
- <2 second API response times
- <1% error rate
- Zero security incidents

**Client Satisfaction:**
- High lead generation success rates
- Fast support response times
- Positive client feedback
- Low churn rate

**Business Growth:**
- Increasing client count
- Growing revenue per client
- Expanding feature usage
- Strong referral rates

Your LeadAI Pro admin system gives you complete control over a scalable, secure, multi-client lead generation platform! 👑

