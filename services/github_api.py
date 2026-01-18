import re
import requests
from urllib.parse import urlparse

def fetch_github_repo(url: str):
    """Fetch repository metadata from GitHub API."""
    # Extract owner/repo from GitHub URL
    github_pattern = r'github\.com/([^/]+)/([^/]+?)(?:/|$|\?|#)'
    match = re.search(github_pattern, url)
    
    if not match:
        return None
    
    owner, repo = match.groups()
    repo = repo.rstrip('/')
    
    try:
        # GitHub API endpoint
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'AutoBib-Tool'
        }
        
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Get contributors to determine primary author
            contributors_url = data.get('contributors_url', '')
            contributors = []
            if contributors_url:
                try:
                    contributors_response = requests.get(contributors_url, headers=headers, timeout=5)
                    if contributors_response.status_code == 200:
                        contributors_data = contributors_response.json()
                        contributors = [contrib.get('login', '') for contrib in contributors_data[:5]]
                except:
                    pass
            
            # Extract language info
            languages_url = data.get('languages_url', '')
            languages = []
            if languages_url:
                try:
                    languages_response = requests.get(languages_url, headers=headers, timeout=5)
                    if languages_response.status_code == 200:
                        languages = list(languages_response.json().keys())
                except:
                    pass
            
            # Extract creation date for year
            created_at = data.get('created_at', '')
            year = created_at[:4] if created_at else ''
            
            return {
                'title': data.get('name', ''),
                'author': contributors or [data.get('owner', {}).get('login', 'Unknown')],
                'year': year,
                'publisher': 'GitHub',
                'version': data.get('default_branch', ''),
                'description': data.get('description', ''),
                'language': ', '.join(languages),
                'stars': data.get('stargazers_count', 0),
                'forks': data.get('forks_count', 0),
                'license': data.get('license', {}).get('name', '') if data.get('license') else '',
                'type': 'software',
                'URL': data.get('html_url', url)
            }
    except Exception as e:
        print(f"GitHub API error: {e}")
    
    return None

def is_github_url(url: str) -> bool:
    """Check if URL is a GitHub repository."""
    return 'github.com' in url and re.search(r'github\.com/[^/]+/[^/]+', url)
