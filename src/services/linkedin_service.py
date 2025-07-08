import requests
import time
import json
import urllib.parse
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class LinkedInService:
    """Service for LinkedIn API integration per client"""
    
    def __init__(self, client_id: str, client_secret: str, access_token: str = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.base_url = "https://api.linkedin.com/v2"
        self.rate_limit_delay = 1  # seconds between requests
        self.last_request_time = 0
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Optional[Dict]:
        """Make rate-limited request to LinkedIn API"""
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        
        url = f"{self.base_url}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, params=params, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # Rate limit exceeded, wait and retry
                print("LinkedIn API rate limit exceeded, waiting 60 seconds...")
                time.sleep(60)
                return self._make_request(method, endpoint, params, data)
            elif response.status_code == 401:
                print("LinkedIn API authentication failed - token may be expired")
                return None
            else:
                print(f"LinkedIn API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error making LinkedIn API request: {e}")
            return None
    
    def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """
        Generate LinkedIn OAuth authorization URL
        
        Args:
            redirect_uri: URL to redirect after authorization
            state: Optional state parameter for security
            
        Returns:
            Authorization URL
        """
        
        scope = "r_liteprofile r_emailaddress w_member_social"
        
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'scope': scope
        }
        
        if state:
            params['state'] = state
        
        query_string = urllib.parse.urlencode(params)
        return f"https://www.linkedin.com/oauth/v2/authorization?{query_string}"
    
    def exchange_code_for_token(self, code: str, redirect_uri: str) -> Optional[Dict]:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from LinkedIn
            redirect_uri: Same redirect URI used in authorization
            
        Returns:
            Token response dictionary
        """
        
        url = "https://www.linkedin.com/oauth/v2/accessToken"
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = requests.post(url, data=data, headers=headers)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                return token_data
            else:
                print(f"Token exchange failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error exchanging code for token: {e}")
            return None
    
    def get_profile(self) -> Optional[Dict]:
        """
        Get current user's LinkedIn profile
        
        Returns:
            Profile data dictionary
        """
        
        if not self.access_token:
            return None
        
        return self._make_request('GET', 'people/~')
    
    def search_people(self, 
                     keywords: str = None,
                     current_company: str = None,
                     past_company: str = None,
                     school: str = None,
                     location: str = None,
                     industry: str = None,
                     start: int = 0,
                     count: int = 10) -> Optional[Dict]:
        """
        Search for people on LinkedIn
        
        Note: This requires LinkedIn Partner Program access
        Most standard LinkedIn APIs don't allow people search
        
        Args:
            keywords: Search keywords
            current_company: Current company name
            past_company: Past company name
            school: School name
            location: Location
            industry: Industry
            start: Start index for pagination
            count: Number of results to return
            
        Returns:
            Search results dictionary
        """
        
        # Note: This endpoint requires special LinkedIn Partner access
        # Standard LinkedIn APIs don't provide people search functionality
        # This is a placeholder for when you have Partner Program access
        
        params = {
            'start': start,
            'count': min(count, 50)  # LinkedIn limits to 50 per request
        }
        
        if keywords:
            params['keywords'] = keywords
        if current_company:
            params['current-company'] = current_company
        if past_company:
            params['past-company'] = past_company
        if school:
            params['school'] = school
        if location:
            params['location'] = location
        if industry:
            params['industry'] = industry
        
        # This endpoint requires LinkedIn Partner Program
        return self._make_request('GET', 'people-search', params=params)
    
    def get_company_info(self, company_id: str) -> Optional[Dict]:
        """
        Get company information by LinkedIn company ID
        
        Args:
            company_id: LinkedIn company ID
            
        Returns:
            Company data dictionary
        """
        
        return self._make_request('GET', f'companies/{company_id}')
    
    def search_companies(self, 
                        keywords: str = None,
                        location: str = None,
                        industry: str = None,
                        company_size: str = None,
                        start: int = 0,
                        count: int = 10) -> Optional[Dict]:
        """
        Search for companies on LinkedIn
        
        Args:
            keywords: Search keywords
            location: Company location
            industry: Industry
            company_size: Company size range
            start: Start index for pagination
            count: Number of results to return
            
        Returns:
            Search results dictionary
        """
        
        params = {
            'start': start,
            'count': min(count, 50)
        }
        
        if keywords:
            params['keywords'] = keywords
        if location:
            params['location'] = location
        if industry:
            params['industry'] = industry
        if company_size:
            params['company-size'] = company_size
        
        return self._make_request('GET', 'company-search', params=params)
    
    def get_connections(self, start: int = 0, count: int = 50) -> Optional[Dict]:
        """
        Get user's LinkedIn connections
        
        Args:
            start: Start index for pagination
            count: Number of connections to return
            
        Returns:
            Connections data dictionary
        """
        
        params = {
            'start': start,
            'count': min(count, 500)  # LinkedIn limits connections API
        }
        
        return self._make_request('GET', 'people/~/connections', params=params)
    
    def send_message(self, recipient_id: str, subject: str, message: str) -> Optional[Dict]:
        """
        Send a message to a LinkedIn connection
        
        Note: This requires special permissions and may be restricted
        
        Args:
            recipient_id: LinkedIn member ID of recipient
            subject: Message subject
            message: Message content
            
        Returns:
            Response dictionary
        """
        
        data = {
            'recipients': {
                'values': [
                    {
                        'person': {
                            'id': recipient_id
                        }
                    }
                ]
            },
            'subject': subject,
            'body': message
        }
        
        return self._make_request('POST', 'people/~/mailbox', data=data)
    
    def validate_token(self) -> bool:
        """
        Validate the current access token
        
        Returns:
            True if token is valid, False otherwise
        """
        
        if not self.access_token:
            return False
        
        profile = self.get_profile()
        return profile is not None


class LinkedInSalesNavigatorService:
    """
    Service for LinkedIn Sales Navigator API (requires special access)
    
    Note: Sales Navigator API requires LinkedIn Sales Navigator subscription
    and special API access approval from LinkedIn
    """
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.linkedin.com/v2"
    
    def advanced_people_search(self, 
                              keywords: str = None,
                              title: str = None,
                              company: str = None,
                              location: str = None,
                              industry: str = None,
                              seniority: str = None,
                              company_size: str = None,
                              years_experience: str = None) -> Optional[Dict]:
        """
        Advanced people search using Sales Navigator API
        
        Note: This requires Sales Navigator subscription and API approval
        
        Args:
            keywords: Search keywords
            title: Job title
            company: Company name
            location: Location
            industry: Industry
            seniority: Seniority level
            company_size: Company size
            years_experience: Years of experience
            
        Returns:
            Search results dictionary
        """
        
        # This is a placeholder for Sales Navigator API
        # Actual implementation requires special LinkedIn approval
        
        search_params = {
            'keywords': keywords,
            'title': title,
            'company': company,
            'location': location,
            'industry': industry,
            'seniority': seniority,
            'company_size': company_size,
            'years_experience': years_experience
        }
        
        # Filter out None values
        search_params = {k: v for k, v in search_params.items() if v is not None}
        
        # This would be the actual API call if you have Sales Navigator access
        # return self._make_request('GET', 'sales-navigator/people-search', params=search_params)
        
        return None  # Placeholder


class LinkedInLeadGenService:
    """
    Service for LinkedIn lead generation using available APIs
    """
    
    def __init__(self, linkedin_service: LinkedInService):
        self.linkedin_service = linkedin_service
    
    def generate_leads_from_companies(self, company_keywords: List[str], 
                                    location: str = "Australia",
                                    max_companies: int = 50) -> List[Dict]:
        """
        Generate leads by finding companies and their employees
        
        Args:
            company_keywords: List of keywords to search for companies
            location: Location filter
            max_companies: Maximum number of companies to process
            
        Returns:
            List of lead dictionaries
        """
        
        leads = []
        
        for keyword in company_keywords:
            print(f"Searching companies with keyword: {keyword}")
            
            companies = self.linkedin_service.search_companies(
                keywords=keyword,
                location=location,
                count=min(max_companies // len(company_keywords), 25)
            )
            
            if not companies or 'elements' not in companies:
                continue
            
            for company in companies['elements']:
                company_id = company.get('id')
                company_name = company.get('name')
                
                if not company_id:
                    continue
                
                # Get company details
                company_details = self.linkedin_service.get_company_info(company_id)
                
                if company_details:
                    # Create lead entry for the company
                    lead = {
                        'type': 'company',
                        'company_name': company_name,
                        'company_id': company_id,
                        'industry': company_details.get('industry'),
                        'location': company_details.get('location'),
                        'employee_count': company_details.get('employeeCountRange'),
                        'description': company_details.get('description'),
                        'website': company_details.get('website'),
                        'source': 'linkedin_company_search',
                        'search_keyword': keyword,
                        'found_at': datetime.utcnow().isoformat()
                    }
                    
                    leads.append(lead)
                
                # Rate limiting
                time.sleep(1)
        
        return leads
    
    def enrich_lead_with_linkedin(self, lead_data: Dict) -> Dict:
        """
        Enrich existing lead data with LinkedIn information
        
        Args:
            lead_data: Existing lead data dictionary
            
        Returns:
            Enriched lead data
        """
        
        company_name = lead_data.get('company')
        
        if not company_name:
            return lead_data
        
        # Search for the company on LinkedIn
        companies = self.linkedin_service.search_companies(
            keywords=company_name,
            count=5
        )
        
        if companies and 'elements' in companies:
            # Find the best matching company
            for company in companies['elements']:
                if company.get('name', '').lower() == company_name.lower():
                    # Get detailed company information
                    company_details = self.linkedin_service.get_company_info(company.get('id'))
                    
                    if company_details:
                        # Enrich the lead data
                        lead_data.update({
                            'linkedin_company_id': company.get('id'),
                            'linkedin_company_url': company_details.get('websiteUrl'),
                            'company_industry': company_details.get('industry'),
                            'company_size': company_details.get('employeeCountRange'),
                            'company_description': company_details.get('description'),
                            'linkedin_enriched': True,
                            'linkedin_enriched_at': datetime.utcnow().isoformat()
                        })
                    
                    break
        
        return lead_data
    
    def get_australian_consultant_companies(self) -> List[Dict]:
        """
        Get Australian consulting companies using LinkedIn API
        
        Returns:
            List of company dictionaries
        """
        
        consulting_keywords = [
            "management consulting",
            "business consulting", 
            "strategy consulting",
            "corporate wellness",
            "leadership coaching",
            "professional services"
        ]
        
        return self.generate_leads_from_companies(
            company_keywords=consulting_keywords,
            location="Australia",
            max_companies=100
        )


# Utility functions for LinkedIn integration
def create_linkedin_oauth_url(client_id: str, redirect_uri: str, state: str = None) -> str:
    """Create LinkedIn OAuth authorization URL"""
    linkedin_service = LinkedInService(client_id, "", "")
    return linkedin_service.get_authorization_url(redirect_uri, state)


def exchange_linkedin_code(client_id: str, client_secret: str, 
                          code: str, redirect_uri: str) -> Optional[Dict]:
    """Exchange LinkedIn authorization code for access token"""
    linkedin_service = LinkedInService(client_id, client_secret, "")
    return linkedin_service.exchange_code_for_token(code, redirect_uri)


def validate_linkedin_token(access_token: str) -> bool:
    """Validate LinkedIn access token"""
    linkedin_service = LinkedInService("", "", access_token)
    return linkedin_service.validate_token()


# Example usage and testing functions
def test_linkedin_service():
    """Test function for LinkedIn service (requires valid credentials)"""
    
    # Note: Replace with actual LinkedIn app credentials
    client_id = "YOUR_LINKEDIN_CLIENT_ID"
    client_secret = "YOUR_LINKEDIN_CLIENT_SECRET"
    access_token = "YOUR_LINKEDIN_ACCESS_TOKEN"
    
    if client_id == "YOUR_LINKEDIN_CLIENT_ID":
        print("Please set valid LinkedIn credentials to test the service")
        return
    
    linkedin = LinkedInService(client_id, client_secret, access_token)
    
    # Test token validation
    if not linkedin.validate_token():
        print("Invalid LinkedIn access token")
        return
    
    print("LinkedIn access token is valid!")
    
    # Test profile retrieval
    profile = linkedin.get_profile()
    if profile:
        print(f"Profile: {profile.get('firstName')} {profile.get('lastName')}")
    
    # Test company search
    companies = linkedin.search_companies(
        keywords="consulting",
        location="Australia",
        count=5
    )
    
    if companies and 'elements' in companies:
        print(f"Found {len(companies['elements'])} companies")
        for company in companies['elements'][:3]:
            print(f"- {company.get('name')}")


if __name__ == "__main__":
    test_linkedin_service()

