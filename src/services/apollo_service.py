import requests
import time
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class ApolloService:
    """Service for interacting with Apollo.io API for automated lead generation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.apollo.io/api/v1"
        self.headers = {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'X-Api-Key': api_key
        }
        self.rate_limit_delay = 1  # seconds between requests
        self.last_request_time = 0
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Optional[Dict]:
        """Make rate-limited request to Apollo API"""
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, params=params, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # Rate limit exceeded, wait and retry
                print("Rate limit exceeded, waiting 60 seconds...")
                time.sleep(60)
                return self._make_request(method, endpoint, params, data)
            else:
                print(f"Apollo API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error making Apollo API request: {e}")
            return None
    
    def search_people(self, 
                     person_titles: List[str] = None,
                     person_locations: List[str] = None,
                     organization_locations: List[str] = None,
                     organization_industries: List[str] = None,
                     organization_num_employees_ranges: List[str] = None,
                     person_seniorities: List[str] = None,
                     per_page: int = 25,
                     page: int = 1) -> Optional[Dict]:
        """
        Search for people using Apollo API with various filters
        
        Args:
            person_titles: List of job titles to search for
            person_locations: List of person locations (e.g., ["Sydney, AU", "Melbourne, AU"])
            organization_locations: List of company locations
            organization_industries: List of industries
            organization_num_employees_ranges: List of employee ranges (e.g., ["1,10", "11,50"])
            person_seniorities: List of seniority levels
            per_page: Number of results per page (1-100)
            page: Page number
        
        Returns:
            Dictionary containing search results
        """
        
        params = {
            'per_page': min(per_page, 100),
            'page': page
        }
        
        # Add filters if provided
        if person_titles:
            for i, title in enumerate(person_titles):
                params[f'person_titles[{i}]'] = title
        
        if person_locations:
            for i, location in enumerate(person_locations):
                params[f'person_locations[{i}]'] = location
        
        if organization_locations:
            for i, location in enumerate(organization_locations):
                params[f'organization_locations[{i}]'] = location
        
        if organization_industries:
            for i, industry in enumerate(organization_industries):
                params[f'organization_industries[{i}]'] = industry
        
        if organization_num_employees_ranges:
            for i, range_val in enumerate(organization_num_employees_ranges):
                params[f'organization_num_employees_ranges[{i}]'] = range_val
        
        if person_seniorities:
            for i, seniority in enumerate(person_seniorities):
                params[f'person_seniorities[{i}]'] = seniority
        
        return self._make_request('POST', 'mixed_people/search', params=params)
    
    def enrich_person(self, email: str = None, first_name: str = None, 
                     last_name: str = None, organization_name: str = None) -> Optional[Dict]:
        """
        Enrich person data using Apollo API
        
        Args:
            email: Person's email address
            first_name: Person's first name
            last_name: Person's last name
            organization_name: Person's company name
        
        Returns:
            Dictionary containing enriched person data
        """
        
        data = {}
        if email:
            data['email'] = email
        if first_name:
            data['first_name'] = first_name
        if last_name:
            data['last_name'] = last_name
        if organization_name:
            data['organization_name'] = organization_name
        
        return self._make_request('POST', 'people/match', data=data)
    
    def search_australian_consultants(self, 
                                    industries: List[str] = None,
                                    cities: List[str] = None,
                                    company_sizes: List[str] = None,
                                    per_page: int = 25) -> Optional[Dict]:
        """
        Specialized search for Australian B2B consultants
        
        Args:
            industries: Target industries (default: consulting-related)
            cities: Australian cities (default: major cities)
            company_sizes: Company size ranges
            per_page: Results per page
        
        Returns:
            Dictionary containing search results
        """
        
        # Default Australian consultant targeting
        if not industries:
            industries = [
                "Management Consulting",
                "Business Consulting",
                "Strategy Consulting",
                "IT Consulting",
                "Financial Consulting",
                "HR Consulting",
                "Marketing Consulting"
            ]
        
        if not cities:
            cities = [
                "Sydney, AU",
                "Melbourne, AU", 
                "Brisbane, AU",
                "Perth, AU",
                "Adelaide, AU",
                "Canberra, AU"
            ]
        
        if not company_sizes:
            company_sizes = ["1,10", "11,50", "51,200", "201,500"]
        
        # Consultant job titles
        consultant_titles = [
            "Consultant",
            "Senior Consultant", 
            "Principal Consultant",
            "Managing Consultant",
            "Director",
            "Managing Director",
            "Partner",
            "Founder",
            "CEO",
            "Business Development Manager",
            "Sales Director"
        ]
        
        # Seniority levels
        seniorities = ["senior", "director", "vp", "c_level", "partner", "owner"]
        
        return self.search_people(
            person_titles=consultant_titles,
            person_locations=cities,
            organization_industries=industries,
            organization_num_employees_ranges=company_sizes,
            person_seniorities=seniorities,
            per_page=per_page
        )
    
    def bulk_search_leads(self, search_configs: List[Dict], max_leads: int = 1000) -> List[Dict]:
        """
        Perform bulk lead searches with multiple configurations
        
        Args:
            search_configs: List of search configuration dictionaries
            max_leads: Maximum number of leads to collect
        
        Returns:
            List of lead dictionaries
        """
        
        all_leads = []
        leads_collected = 0
        
        for config in search_configs:
            if leads_collected >= max_leads:
                break
            
            page = 1
            while leads_collected < max_leads:
                remaining_leads = max_leads - leads_collected
                per_page = min(25, remaining_leads)
                
                print(f"Searching with config: {config.get('name', 'Unnamed')} - Page {page}")
                
                result = self.search_people(
                    person_titles=config.get('person_titles'),
                    person_locations=config.get('person_locations'),
                    organization_locations=config.get('organization_locations'),
                    organization_industries=config.get('organization_industries'),
                    organization_num_employees_ranges=config.get('organization_num_employees_ranges'),
                    person_seniorities=config.get('person_seniorities'),
                    per_page=per_page,
                    page=page
                )
                
                if not result or 'people' not in result:
                    print(f"No results for config: {config.get('name', 'Unnamed')}")
                    break
                
                people = result['people']
                if not people:
                    print(f"No more results for config: {config.get('name', 'Unnamed')}")
                    break
                
                # Add source information to each lead
                for person in people:
                    person['search_config'] = config.get('name', 'Unknown')
                    person['search_timestamp'] = datetime.utcnow().isoformat()
                
                all_leads.extend(people)
                leads_collected += len(people)
                
                print(f"Collected {len(people)} leads. Total: {leads_collected}")
                
                # Check if we have more pages
                pagination = result.get('pagination', {})
                if page >= pagination.get('total_pages', 1):
                    break
                
                page += 1
                
                # Rate limiting between pages
                time.sleep(2)
        
        print(f"Bulk search completed. Total leads collected: {len(all_leads)}")
        return all_leads
    
    def get_default_australian_search_configs(self) -> List[Dict]:
        """
        Get default search configurations for Australian B2B consultants
        
        Returns:
            List of search configuration dictionaries
        """
        
        return [
            {
                'name': 'Sydney Corporate Wellness Consultants',
                'person_titles': ['Consultant', 'Senior Consultant', 'Director', 'Managing Director'],
                'person_locations': ['Sydney, AU'],
                'organization_industries': ['Wellness', 'Health', 'Corporate Wellness', 'Employee Benefits'],
                'organization_num_employees_ranges': ['11,50', '51,200', '201,500'],
                'person_seniorities': ['senior', 'director', 'vp']
            },
            {
                'name': 'Melbourne Leadership Coaches',
                'person_titles': ['Coach', 'Leadership Coach', 'Executive Coach', 'Consultant'],
                'person_locations': ['Melbourne, AU'],
                'organization_industries': ['Coaching', 'Leadership Development', 'Training', 'Professional Development'],
                'organization_num_employees_ranges': ['1,10', '11,50', '51,200'],
                'person_seniorities': ['senior', 'director', 'owner']
            },
            {
                'name': 'Brisbane Business Consultants',
                'person_titles': ['Business Consultant', 'Strategy Consultant', 'Management Consultant'],
                'person_locations': ['Brisbane, AU'],
                'organization_industries': ['Management Consulting', 'Business Consulting', 'Strategy'],
                'organization_num_employees_ranges': ['1,10', '11,50', '51,200'],
                'person_seniorities': ['senior', 'director', 'partner']
            },
            {
                'name': 'Perth Strategic Advisors',
                'person_titles': ['Strategic Advisor', 'Business Advisor', 'Consultant', 'Director'],
                'person_locations': ['Perth, AU'],
                'organization_industries': ['Strategic Consulting', 'Business Advisory', 'Financial Advisory'],
                'organization_num_employees_ranges': ['1,10', '11,50'],
                'person_seniorities': ['senior', 'director', 'c_level']
            },
            {
                'name': 'Adelaide Professional Services',
                'person_titles': ['Consultant', 'Senior Consultant', 'Principal', 'Director'],
                'person_locations': ['Adelaide, AU'],
                'organization_industries': ['Professional Services', 'Consulting', 'Advisory Services'],
                'organization_num_employees_ranges': ['1,10', '11,50', '51,200'],
                'person_seniorities': ['senior', 'director']
            }
        ]
    
    def validate_api_key(self) -> bool:
        """
        Validate the Apollo API key
        
        Returns:
            True if API key is valid, False otherwise
        """
        
        # Try a simple search to validate the API key
        result = self.search_people(
            person_titles=['CEO'],
            person_locations=['Sydney, AU'],
            per_page=1
        )
        
        return result is not None and 'people' in result


# Example usage and testing functions
def test_apollo_service():
    """Test function for Apollo service (requires valid API key)"""
    
    # Note: Replace with actual API key for testing
    api_key = "YOUR_APOLLO_API_KEY"
    
    if api_key == "YOUR_APOLLO_API_KEY":
        print("Please set a valid Apollo API key to test the service")
        return
    
    apollo = ApolloService(api_key)
    
    # Test API key validation
    if not apollo.validate_api_key():
        print("Invalid Apollo API key")
        return
    
    print("Apollo API key is valid!")
    
    # Test Australian consultant search
    print("Searching for Australian consultants...")
    result = apollo.search_australian_consultants(per_page=5)
    
    if result and 'people' in result:
        print(f"Found {len(result['people'])} consultants")
        for person in result['people'][:3]:  # Show first 3
            print(f"- {person.get('name', 'Unknown')} at {person.get('organization', {}).get('name', 'Unknown Company')}")
    else:
        print("No results found")


if __name__ == "__main__":
    test_apollo_service()

