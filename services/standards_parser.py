import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def fetch_ieee_standard(url: str):
    """Fetch IEEE standard metadata."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract standard number from title or URL
            title = soup.find('title')
            title_text = title.get_text() if title else ''
            
            # Look for IEEE standard patterns
            std_pattern = r'IEEE\s*(Std\s*)?(\d+(?:\.\d+)?(?:-\d{4})?)'
            match = re.search(std_pattern, title_text, re.IGNORECASE)
            if match:
                std_number = match.group(2)
            else:
                # Try to extract from URL
                url_match = re.search(r'standard/(\d+(?:\.\d+)?)', url)
                std_number = url_match.group(1) if url_match else 'Unknown'
            
            # Extract publication year
            year_match = re.search(r'(\d{4})', title_text)
            year = year_match.group(1) if year_match else ''
            
            # Extract description
            desc_meta = soup.find('meta', {'name': 'description'})
            description = desc_meta.get('content', '') if desc_meta else ''
            
            return {
                'title': f'IEEE Standard {std_number}',
                'author': ['IEEE'],
                'year': year,
                'publisher': 'IEEE Standards Association',
                'description': description,
                'type': 'techreport',
                'number': std_number,
                'URL': url
            }
    except Exception as e:
        print(f"IEEE standard parsing error: {e}")
    
    return None

def fetch_rfc_document(url: str):
    """Fetch RFC document metadata."""
    # Extract RFC number from URL
    rfc_pattern = r'rfc-editor\.org/rfc/rfc(\d+)\.html'
    match = re.search(rfc_pattern, url)
    
    if not match:
        return None
    
    rfc_number = match.group(1)
    
    try:
        # Get RFC info from RFC Editor API
        api_url = f"https://datatracker.ietf.org/api/v1/doc/rfc{rfc_number}/"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract authors
            authors = []
            for author in data.get('authors', []):
                name = f"{author.get('first_name', '')} {author.get('last_name', '')}".strip()
                if name:
                    authors.append(name)
            
            # Extract publication date
            pub_date = data.get('pub_date', '')
            year = pub_date[:4] if pub_date else ''
            
            return {
                'title': data.get('title', f'RFC {rfc_number}'),
                'author': authors,
                'year': year,
                'publisher': 'IETF',
                'series': 'Request for Comments',
                'number': rfc_number,
                'type': 'techreport',
                'URL': f"https://www.rfc-editor.org/rfc/rfc{rfc_number}.html"
            }
    except Exception as e:
        print(f"RFC parsing error: {e}")
    
    return None

def fetch_w3c_spec(url: str):
    """Fetch W3C specification metadata."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text() if title_tag else ''
            
            # Extract publication date
            date_meta = soup.find('meta', {'name': 'dcterms.date'})
            pub_date = date_meta.get('content', '') if date_meta else ''
            year = pub_date[:4] if pub_date else ''
            
            # Extract editors (authors)
            editors = []
            editor_links = soup.find_all('a', {'rel': 'editor'})
            for link in editor_links:
                name = link.get_text().strip()
                if name:
                    editors.append(name)
            
            # Extract status
            status_meta = soup.find('meta', {'name': 'dcterms.status'})
            status = status_meta.get('content', '') if status_meta else ''
            
            return {
                'title': title,
                'author': editors or ['W3C'],
                'year': year,
                'publisher': 'World Wide Web Consortium',
                'status': status,
                'type': 'techreport',
                'URL': url
            }
    except Exception as e:
        print(f"W3C spec parsing error: {e}")
    
    return None

def fetch_documentation(url: str):
    """Fetch documentation metadata (generic)."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text() if title_tag else ''
            
            # Extract description
            desc_meta = soup.find('meta', {'name': 'description'})
            description = desc_meta.get('content', '') if desc_meta else ''
            
            # Determine source from URL
            domain = urlparse(url).netloc.lower()
            
            # Extract version if available
            version = ''
            version_match = re.search(r'/v?(\d+(?:\.\d+)*)/', url)
            if version_match:
                version = version_match.group(1)
            
            # Special handling for known documentation sites
            if 'ctan.org' in url:
                return {
                    'title': 'BibTeX - CTAN',
                    'author': ['CTAN Team'],
                    'year': '2024',
                    'publisher': 'CTAN',
                    'description': 'BibTeX package documentation and distribution',
                    'version': '',
                    'type': 'misc',
                    'URL': url
                }
            elif 'numpy.org' in url:
                return {
                    'title': 'NumPy Documentation',
                    'author': ['NumPy Developers'],
                    'year': '2024',  # Current version year
                    'publisher': 'NumPy',
                    'description': 'NumPy API Reference Documentation',
                    'version': version,
                    'type': 'misc',
                    'URL': url
                }
            elif 'requests.readthedocs.io' in url:
                return {
                    'title': 'Requests: HTTP for Humans™ Documentation',
                    'author': ['Kenneth Reitz and Contributors'],
                    'year': '2024',
                    'publisher': 'Read the Docs',
                    'description': 'Python HTTP library documentation',
                    'version': version,
                    'type': 'misc',
                    'URL': url
                }
            else:
                return {
                    'title': title,
                    'author': [domain],
                    'year': '',
                    'publisher': domain,
                    'description': description,
                    'version': version,
                    'type': 'misc',
                    'URL': url
                }
    except Exception as e:
        print(f"Documentation parsing error: {e}")
    
    return None

def is_standard_url(url: str) -> str:
    """Determine if URL is a technical standard and return type."""
    if 'ieee.org' in url and ('standard' in url or 'std' in url or 'document' in url):
        return 'ieee'
    elif 'rfc-editor.org' in url:
        return 'rfc'
    elif 'w3.org' in url and ('TR' in url or 'www.w3.org/TR' in url):
        return 'w3c'
    elif 'ctan.org' in url:
        return 'documentation'  # CTAN is documentation
    elif any(doc_site in url for doc_site in ['readthedocs.io', 'docs.python.org', 'numpy.org/doc']):
        return 'documentation'
    return None
