import requests
import time
import json
from typing import Dict, Optional, List
from datetime import datetime

class EnrichmentService:
    """Service for enriching lead data using various APIs"""
    
    def __init__(self, hunter_api_key: str = None):
        self.hunter_api_key = hunter_api_key
        self.hunter_base_url = "https://api.hunter.io/v2"
        self.rate_limit_delay = 1  # seconds between requests
        self.last_request_time = 0
    
    def _make_hunter_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make rate-limited request to Hunter.io API"""
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        
        if not params:
            params = {}
        params['api_key'] = self.hunter_api_key
        
        url = f"{self.hunter_base_url}/{endpoint}"
        
        try:
            response = requests.get(url, params=params)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # Rate limit exceeded, wait and retry
                print("Hunter.io rate limit exceeded, waiting 60 seconds...")
                time.sleep(60)
                return self._make_hunter_request(endpoint, params)
            else:
                print(f"Hunter.io API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error making Hunter.io API request: {e}")
            return None
    
    def verify_email(self, email: str) -> Optional[Dict]:
        """
        Verify email address using Hunter.io
        
        Args:
            email: Email address to verify
            
        Returns:
            Dictionary with verification results
        """
        
        if not self.hunter_api_key:
            return None
        
        result = self._make_hunter_request('email-verifier', {'email': email})
        
        if result and 'data' in result:
            data = result['data']
            return {
                'email': email,
                'status': data.get('status'),
                'result': data.get('result'),
                'score': data.get('score'),
                'regexp': data.get('regexp'),
                'gibberish': data.get('gibberish'),
                'disposable': data.get('disposable'),
                'webmail': data.get('webmail'),
                'mx_records': data.get('mx_records'),
                'smtp_server': data.get('smtp_server'),
                'smtp_check': data.get('smtp_check'),
                'accept_all': data.get('accept_all'),
                'block': data.get('block')
            }
        
        return None
    
    def find_email(self, first_name: str, last_name: str, domain: str) -> Optional[Dict]:
        """
        Find email address using Hunter.io Email Finder
        
        Args:
            first_name: Person's first name
            last_name: Person's last name
            domain: Company domain
            
        Returns:
            Dictionary with email finding results
        """
        
        if not self.hunter_api_key:
            return None
        
        params = {
            'first_name': first_name,
            'last_name': last_name,
            'domain': domain
        }
        
        result = self._make_hunter_request('email-finder', params)
        
        if result and 'data' in result:
            data = result['data']
            return {
                'email': data.get('email'),
                'score': data.get('score'),
                'first_name': data.get('first_name'),
                'last_name': data.get('last_name'),
                'position': data.get('position'),
                'twitter': data.get('twitter'),
                'linkedin_url': data.get('linkedin_url'),
                'phone_number': data.get('phone_number'),
                'company': data.get('company'),
                'sources': data.get('sources', [])
            }
        
        return None
    
    def get_domain_emails(self, domain: str, limit: int = 10) -> Optional[List[Dict]]:
        """
        Get all emails from a domain using Hunter.io Domain Search
        
        Args:
            domain: Company domain to search
            limit: Maximum number of emails to return
            
        Returns:
            List of email dictionaries
        """
        
        if not self.hunter_api_key:
            return None
        
        params = {
            'domain': domain,
            'limit': limit
        }
        
        result = self._make_hunter_request('domain-search', params)
        
        if result and 'data' in result:
            data = result['data']
            emails = []
            
            for email_data in data.get('emails', []):
                emails.append({
                    'email': email_data.get('value'),
                    'type': email_data.get('type'),
                    'confidence': email_data.get('confidence'),
                    'first_name': email_data.get('first_name'),
                    'last_name': email_data.get('last_name'),
                    'position': email_data.get('position'),
                    'seniority': email_data.get('seniority'),
                    'department': email_data.get('department'),
                    'linkedin': email_data.get('linkedin'),
                    'twitter': email_data.get('twitter'),
                    'phone_number': email_data.get('phone_number')
                })
            
            return emails
        
        return None
    
    def enrich_lead(self, email: str) -> Optional[Dict]:
        """
        Comprehensive lead enrichment using multiple data sources
        
        Args:
            email: Lead's email address
            
        Returns:
            Dictionary with enriched lead data
        """
        
        enrichment_data = {
            'email': email,
            'enriched_at': datetime.utcnow().isoformat(),
            'sources': []
        }
        
        # Email verification
        if self.hunter_api_key:
            verification = self.verify_email(email)
            if verification:
                enrichment_data['email_verification'] = verification
                enrichment_data['email_verified'] = verification.get('result') == 'deliverable'
                enrichment_data['sources'].append('hunter_verification')
        
        # Extract domain for additional searches
        domain = email.split('@')[1] if '@' in email else None
        
        if domain and self.hunter_api_key:
            # Get company information from domain
            domain_info = self.get_domain_info(domain)
            if domain_info:
                enrichment_data['company'] = domain_info
                enrichment_data['sources'].append('hunter_domain')
        
        # Social media enrichment (placeholder for future implementation)
        social_data = self._enrich_social_profiles(email)
        if social_data:
            enrichment_data['social'] = social_data
            enrichment_data['sources'].append('social_lookup')
        
        return enrichment_data if enrichment_data['sources'] else None
    
    def get_domain_info(self, domain: str) -> Optional[Dict]:
        """
        Get company information from domain
        
        Args:
            domain: Company domain
            
        Returns:
            Dictionary with company information
        """
        
        if not self.hunter_api_key:
            return None
        
        # Use domain search to get company info
        result = self._make_hunter_request('domain-search', {'domain': domain, 'limit': 1})
        
        if result and 'data' in result:
            data = result['data']
            return {
                'name': data.get('organization'),
                'domain': data.get('domain'),
                'disposable': data.get('disposable'),
                'webmail': data.get('webmail'),
                'accept_all': data.get('accept_all'),
                'pattern': data.get('pattern'),
                'country': data.get('country'),
                'state': data.get('state'),
                'employees': self._estimate_company_size(len(data.get('emails', []))),
                'industry': self._guess_industry_from_domain(domain)
            }
        
        return None
    
    def _estimate_company_size(self, email_count: int) -> str:
        """
        Estimate company size based on number of public emails
        
        Args:
            email_count: Number of public emails found
            
        Returns:
            Company size category
        """
        
        if email_count >= 100:
            return "large"
        elif email_count >= 20:
            return "medium"
        elif email_count >= 5:
            return "small"
        else:
            return "startup"
    
    def _guess_industry_from_domain(self, domain: str) -> Optional[str]:
        """
        Guess industry from domain name (basic implementation)
        
        Args:
            domain: Company domain
            
        Returns:
            Industry guess or None
        """
        
        domain_lower = domain.lower()
        
        industry_keywords = {
            'consulting': ['consult', 'advisory', 'strategy'],
            'technology': ['tech', 'software', 'digital', 'app', 'dev'],
            'healthcare': ['health', 'medical', 'care', 'clinic'],
            'finance': ['finance', 'bank', 'invest', 'capital'],
            'education': ['edu', 'school', 'university', 'learn'],
            'marketing': ['marketing', 'agency', 'creative', 'design'],
            'legal': ['law', 'legal', 'attorney'],
            'real_estate': ['realty', 'property', 'real', 'estate']
        }
        
        for industry, keywords in industry_keywords.items():
            if any(keyword in domain_lower for keyword in keywords):
                return industry
        
        return None
    
    def _enrich_social_profiles(self, email: str) -> Optional[Dict]:
        """
        Enrich with social media profiles (placeholder implementation)
        
        Args:
            email: Email address
            
        Returns:
            Dictionary with social profiles or None
        """
        
        # This is a placeholder for social media enrichment
        # In a real implementation, you would integrate with services like:
        # - Clearbit
        # - FullContact
        # - Pipl
        # - Social media APIs
        
        return None
    
    def bulk_enrich_leads(self, emails: List[str], max_concurrent: int = 3) -> List[Dict]:
        """
        Bulk enrich multiple leads
        
        Args:
            emails: List of email addresses
            max_concurrent: Maximum concurrent API calls
            
        Returns:
            List of enrichment results
        """
        
        results = []
        
        for i, email in enumerate(emails):
            print(f"Enriching lead {i+1}/{len(emails)}: {email}")
            
            enrichment = self.enrich_lead(email)
            if enrichment:
                results.append(enrichment)
            
            # Rate limiting
            if i < len(emails) - 1:  # Don't sleep after the last request
                time.sleep(self.rate_limit_delay)
        
        return results
    
    def validate_hunter_api_key(self) -> bool:
        """
        Validate Hunter.io API key
        
        Returns:
            True if API key is valid, False otherwise
        """
        
        if not self.hunter_api_key:
            return False
        
        # Try to get account information
        result = self._make_hunter_request('account')
        return result is not None and 'data' in result


class LinkedInEnrichmentService:
    """Service for LinkedIn-based lead enrichment (placeholder)"""
    
    def __init__(self, linkedin_api_key: str = None):
        self.linkedin_api_key = linkedin_api_key
        # Note: LinkedIn has strict API access requirements
        # This is a placeholder for future implementation
    
    def enrich_from_linkedin_url(self, linkedin_url: str) -> Optional[Dict]:
        """
        Enrich lead data from LinkedIn profile URL
        
        Args:
            linkedin_url: LinkedIn profile URL
            
        Returns:
            Dictionary with LinkedIn data or None
        """
        
        # Placeholder implementation
        # In practice, you would need:
        # 1. LinkedIn API access (requires partnership)
        # 2. Web scraping (against ToS)
        # 3. Third-party services like Proxycurl
        
        return None
    
    def search_linkedin_profiles(self, company: str, title: str) -> List[Dict]:
        """
        Search for LinkedIn profiles by company and title
        
        Args:
            company: Company name
            title: Job title
            
        Returns:
            List of LinkedIn profile data
        """
        
        # Placeholder implementation
        return []


# Example usage and testing
def test_enrichment_service():
    """Test function for enrichment service"""
    
    hunter_api_key = "YOUR_HUNTER_API_KEY"
    
    if hunter_api_key == "YOUR_HUNTER_API_KEY":
        print("Please set a valid Hunter.io API key to test the service")
        return
    
    enrichment = EnrichmentService(hunter_api_key)
    
    # Test API key validation
    if not enrichment.validate_hunter_api_key():
        print("Invalid Hunter.io API key")
        return
    
    print("Hunter.io API key is valid!")
    
    # Test email verification
    test_email = "test@example.com"
    verification = enrichment.verify_email(test_email)
    if verification:
        print(f"Email verification for {test_email}: {verification['result']}")
    
    # Test domain search
    domain_info = enrichment.get_domain_info("apollo.io")
    if domain_info:
        print(f"Domain info for apollo.io: {domain_info['name']}")


if __name__ == "__main__":
    test_enrichment_service()

