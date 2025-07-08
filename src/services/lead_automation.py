import os
import sys
import json
import time
import schedule
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.services.apollo_service import ApolloService
from src.services.enrichment_service import EnrichmentService
from src.models.lead import Lead, LeadCampaign, LeadSource, db
from flask import current_app

class LeadAutomationService:
    """Main service for orchestrating automated lead generation"""
    
    def __init__(self, apollo_api_key: str = None, hunter_api_key: str = None):
        self.apollo_api_key = apollo_api_key or os.getenv('APOLLO_API_KEY')
        self.hunter_api_key = hunter_api_key or os.getenv('HUNTER_API_KEY')
        
        # Initialize services
        if self.apollo_api_key:
            self.apollo_service = ApolloService(self.apollo_api_key)
        else:
            self.apollo_service = None
            print("Warning: Apollo API key not provided")
        
        if self.hunter_api_key:
            self.enrichment_service = EnrichmentService(self.hunter_api_key)
        else:
            self.enrichment_service = None
            print("Warning: Hunter API key not provided")
        
        self.max_workers = 3  # Concurrent workers for API calls
        self.daily_lead_limit = 500  # Daily limit to avoid excessive API usage
        
    def run_campaign(self, campaign_id: int) -> Dict:
        """
        Run a specific lead generation campaign
        
        Args:
            campaign_id: ID of the campaign to run
            
        Returns:
            Dictionary with campaign results
        """
        
        try:
            # Get campaign from database
            campaign = LeadCampaign.query.get(campaign_id)
            if not campaign:
                return {'error': 'Campaign not found', 'success': False}
            
            if campaign.status != 'active':
                return {'error': 'Campaign is not active', 'success': False}
            
            print(f"Starting campaign: {campaign.name}")
            
            # Check daily limits
            today = datetime.utcnow().date()
            today_leads = Lead.query.filter(
                Lead.created_at >= today,
                Lead.auto_generated == True
            ).count()
            
            if today_leads >= self.daily_lead_limit:
                return {
                    'error': f'Daily lead limit reached ({self.daily_lead_limit})',
                    'success': False
                }
            
            remaining_quota = self.daily_lead_limit - today_leads
            leads_to_generate = min(
                campaign.leads_target - campaign.leads_generated,
                remaining_quota
            )
            
            if leads_to_generate <= 0:
                return {
                    'message': 'Campaign target reached or no quota remaining',
                    'success': True,
                    'leads_generated': 0
                }
            
            # Build search configuration from campaign
            search_config = self._build_search_config_from_campaign(campaign)
            
            # Generate leads
            results = self._generate_leads_from_config(search_config, leads_to_generate)
            
            # Update campaign
            campaign.leads_generated += results['leads_saved']
            campaign.last_run = datetime.utcnow()
            
            if campaign.leads_generated >= campaign.leads_target:
                campaign.status = 'completed'
            
            db.session.commit()
            
            return {
                'success': True,
                'campaign_name': campaign.name,
                'leads_generated': results['leads_saved'],
                'leads_enriched': results['leads_enriched'],
                'total_campaign_leads': campaign.leads_generated,
                'campaign_status': campaign.status
            }
            
        except Exception as e:
            print(f"Error running campaign {campaign_id}: {e}")
            return {'error': str(e), 'success': False}
    
    def run_all_active_campaigns(self) -> List[Dict]:
        """
        Run all active campaigns
        
        Returns:
            List of campaign results
        """
        
        active_campaigns = LeadCampaign.query.filter_by(status='active').all()
        results = []
        
        for campaign in active_campaigns:
            result = self.run_campaign(campaign.id)
            result['campaign_id'] = campaign.id
            results.append(result)
            
            # Rate limiting between campaigns
            time.sleep(5)
        
        return results
    
    def generate_australian_consultant_leads(self, max_leads: int = 100) -> Dict:
        """
        Generate leads specifically for Australian B2B consultants
        
        Args:
            max_leads: Maximum number of leads to generate
            
        Returns:
            Dictionary with generation results
        """
        
        if not self.apollo_service:
            return {'error': 'Apollo service not available', 'success': False}
        
        print(f"Generating {max_leads} Australian consultant leads...")
        
        # Get default search configurations
        search_configs = self.apollo_service.get_default_australian_search_configs()
        
        # Distribute leads across configurations
        leads_per_config = max_leads // len(search_configs)
        total_leads_saved = 0
        total_leads_enriched = 0
        
        for config in search_configs:
            try:
                print(f"Processing config: {config['name']}")
                
                result = self._generate_leads_from_config(config, leads_per_config)
                total_leads_saved += result['leads_saved']
                total_leads_enriched += result['leads_enriched']
                
                # Rate limiting between configs
                time.sleep(3)
                
            except Exception as e:
                print(f"Error processing config {config['name']}: {e}")
                continue
        
        return {
            'success': True,
            'total_leads_saved': total_leads_saved,
            'total_leads_enriched': total_leads_enriched,
            'configs_processed': len(search_configs)
        }
    
    def _generate_leads_from_config(self, config: Dict, max_leads: int) -> Dict:
        """
        Generate leads from a single search configuration
        
        Args:
            config: Search configuration dictionary
            max_leads: Maximum leads to generate
            
        Returns:
            Dictionary with results
        """
        
        leads_saved = 0
        leads_enriched = 0
        
        try:
            # Search for people using Apollo
            apollo_results = self.apollo_service.search_people(
                person_titles=config.get('person_titles'),
                person_locations=config.get('person_locations'),
                organization_locations=config.get('organization_locations'),
                organization_industries=config.get('organization_industries'),
                organization_num_employees_ranges=config.get('organization_num_employees_ranges'),
                person_seniorities=config.get('person_seniorities'),
                per_page=min(max_leads, 25)
            )
            
            if not apollo_results or 'people' not in apollo_results:
                return {'leads_saved': 0, 'leads_enriched': 0}
            
            people = apollo_results['people'][:max_leads]
            
            # Process leads in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_person = {
                    executor.submit(self._process_single_lead, person, config): person 
                    for person in people
                }
                
                for future in as_completed(future_to_person):
                    try:
                        result = future.result()
                        if result['saved']:
                            leads_saved += 1
                        if result['enriched']:
                            leads_enriched += 1
                    except Exception as e:
                        print(f"Error processing lead: {e}")
                        continue
            
        except Exception as e:
            print(f"Error in _generate_leads_from_config: {e}")
        
        return {
            'leads_saved': leads_saved,
            'leads_enriched': leads_enriched
        }
    
    def _process_single_lead(self, person_data: Dict, config: Dict) -> Dict:
        """
        Process a single lead: create, enrich, and save
        
        Args:
            person_data: Apollo person data
            config: Search configuration
            
        Returns:
            Dictionary with processing results
        """
        
        try:
            # Check if lead already exists
            email = person_data.get('email')
            if email and Lead.query.filter_by(email=email).first():
                return {'saved': False, 'enriched': False, 'reason': 'duplicate'}
            
            # Create lead from Apollo data
            lead = Lead.from_apollo_data(person_data)
            if not lead:
                return {'saved': False, 'enriched': False, 'reason': 'creation_failed'}
            
            # Add config information
            tags = json.loads(lead.tags) if lead.tags else []
            tags.append(config.get('name', 'unknown_config'))
            lead.tags = json.dumps(tags)
            
            # Enrich lead if enrichment service is available
            enriched = False
            if self.enrichment_service and lead.email:
                try:
                    enrichment_data = self.enrichment_service.enrich_lead(lead.email)
                    if enrichment_data:
                        self._apply_enrichment_data(lead, enrichment_data)
                        lead.enriched = True
                        enriched = True
                except Exception as e:
                    print(f"Enrichment failed for {lead.email}: {e}")
            
            # Save to database
            db.session.add(lead)
            db.session.commit()
            
            return {'saved': True, 'enriched': enriched, 'lead_id': lead.id}
            
        except Exception as e:
            print(f"Error processing single lead: {e}")
            db.session.rollback()
            return {'saved': False, 'enriched': False, 'reason': str(e)}
    
    def _apply_enrichment_data(self, lead: Lead, enrichment_data: Dict):
        """
        Apply enrichment data to a lead
        
        Args:
            lead: Lead object to enrich
            enrichment_data: Enrichment data dictionary
        """
        
        # Update phone if not present
        if not lead.phone and enrichment_data.get('phone'):
            lead.phone = enrichment_data['phone']
        
        # Update company information
        if enrichment_data.get('company'):
            company_data = enrichment_data['company']
            if not lead.company and company_data.get('name'):
                lead.company = company_data['name']
            if not lead.industry and company_data.get('industry'):
                lead.industry = company_data['industry']
            if not lead.employees and company_data.get('employees'):
                lead.employees = company_data['employees']
        
        # Update social profiles
        if enrichment_data.get('linkedin_url') and not lead.linkedin_url:
            lead.linkedin_url = enrichment_data['linkedin_url']
        
        # Add enrichment tags
        tags = json.loads(lead.tags) if lead.tags else []
        tags.append('enriched')
        lead.tags = json.dumps(tags)
        
        # Update verification status
        if enrichment_data.get('email_verified'):
            lead.verified = True
    
    def _build_search_config_from_campaign(self, campaign: LeadCampaign) -> Dict:
        """
        Build Apollo search configuration from campaign settings
        
        Args:
            campaign: LeadCampaign object
            
        Returns:
            Search configuration dictionary
        """
        
        config = {
            'name': campaign.name,
            'person_titles': json.loads(campaign.target_titles) if campaign.target_titles else None,
            'person_locations': [campaign.target_location] if campaign.target_location else None,
            'organization_industries': [campaign.target_industry] if campaign.target_industry else None
        }
        
        # Convert company size to employee ranges
        if campaign.target_company_size:
            size_mapping = {
                'startup': ['1,10'],
                'small': ['11,50'],
                'medium': ['51,200'],
                'large': ['201,1000'],
                'enterprise': ['1001,10000']
            }
            config['organization_num_employees_ranges'] = size_mapping.get(
                campaign.target_company_size.lower(), 
                ['1,50']
            )
        
        return config
    
    def schedule_daily_automation(self):
        """
        Schedule daily automated lead generation
        """
        
        def daily_job():
            print(f"Running daily lead automation at {datetime.now()}")
            results = self.run_all_active_campaigns()
            
            total_leads = sum(r.get('leads_generated', 0) for r in results)
            print(f"Daily automation completed. Total leads generated: {total_leads}")
            
            # Log results to database or file
            self._log_automation_results(results)
        
        # Schedule for 9 AM daily
        schedule.every().day.at("09:00").do(daily_job)
        
        print("Daily automation scheduled for 9:00 AM")
    
    def _log_automation_results(self, results: List[Dict]):
        """
        Log automation results for monitoring
        
        Args:
            results: List of campaign results
        """
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'results': results,
            'total_leads': sum(r.get('leads_generated', 0) for r in results),
            'successful_campaigns': len([r for r in results if r.get('success')])
        }
        
        # Save to log file
        log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'automation.log')
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_automation_stats(self) -> Dict:
        """
        Get automation statistics
        
        Returns:
            Dictionary with automation stats
        """
        
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        stats = {
            'total_leads': Lead.query.filter_by(auto_generated=True).count(),
            'today_leads': Lead.query.filter(
                Lead.created_at >= today,
                Lead.auto_generated == True
            ).count(),
            'week_leads': Lead.query.filter(
                Lead.created_at >= week_ago,
                Lead.auto_generated == True
            ).count(),
            'month_leads': Lead.query.filter(
                Lead.created_at >= month_ago,
                Lead.auto_generated == True
            ).count(),
            'active_campaigns': LeadCampaign.query.filter_by(status='active').count(),
            'completed_campaigns': LeadCampaign.query.filter_by(status='completed').count(),
            'avg_lead_score': db.session.query(db.func.avg(Lead.score)).filter_by(auto_generated=True).scalar() or 0,
            'high_score_leads': Lead.query.filter(
                Lead.score >= 80,
                Lead.auto_generated == True
            ).count()
        }
        
        return stats


# Utility functions for setup and testing
def create_sample_campaign(automation_service: LeadAutomationService) -> int:
    """
    Create a sample campaign for testing
    
    Args:
        automation_service: LeadAutomationService instance
        
    Returns:
        Campaign ID
    """
    
    campaign = LeadCampaign(
        name="Sydney Corporate Wellness Leads",
        description="Target corporate wellness consultants in Sydney",
        target_industry="Corporate Wellness",
        target_location="Sydney, AU",
        target_company_size="medium",
        target_titles=json.dumps([
            "Consultant", "Senior Consultant", "Director", 
            "Managing Director", "Wellness Consultant"
        ]),
        leads_target=50,
        api_source="apollo",
        auto_enrich=True,
        auto_score=True
    )
    
    db.session.add(campaign)
    db.session.commit()
    
    return campaign.id


if __name__ == "__main__":
    # Example usage
    automation = LeadAutomationService()
    
    # Test Australian consultant lead generation
    if automation.apollo_service:
        result = automation.generate_australian_consultant_leads(max_leads=10)
        print(f"Lead generation result: {result}")
    else:
        print("Apollo service not available. Please set APOLLO_API_KEY environment variable.")

