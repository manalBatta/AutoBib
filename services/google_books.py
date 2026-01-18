import re
import requests

def fetch_google_books(isbn: str = None, title: str = None):
    """Fetch book metadata from Google Books API."""
    base_url = "https://www.googleapis.com/books/v1/volumes"
    
    # Try ISBN first if available
    if isbn:
        query = f"isbn:{isbn}"
    elif title:
        query = f"intitle:{title}"
    else:
        return None
    
    try:
        params = {
            'q': query,
            'maxResults': 1,
            'printType': 'books'
        }
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('totalItems', 0) > 0:
                book = data['items'][0]['volumeInfo']
                
                # Extract authors
                authors = book.get('authors', [])
                if not authors:
                    authors = ['Unknown']
                
                # Extract publication info
                pub_info = book.get('publishedDate', '')
                year = re.search(r'\d{4}', pub_info)
                year = year.group() if year else ''
                
                # Extract ISBN
                isbn_13 = None
                isbn_10 = None
                for identifier in book.get('industryIdentifiers', []):
                    if identifier['type'] == 'ISBN_13':
                        isbn_13 = identifier['identifier']
                    elif identifier['type'] == 'ISBN_10':
                        isbn_10 = identifier['identifier']
                
                return {
                    'title': book.get('title', 'Unknown'),
                    'author': authors,
                    'year': year,
                    'publisher': book.get('publisher', ''),
                    'isbn': isbn_13 or isbn_10,
                    'pages': book.get('pageCount', ''),
                    'language': book.get('language', ''),
                    'type': 'book',
                    'URL': book.get('infoLink', '')
                }
    except Exception as e:
        print(f"Google Books API error: {e}")
    
    return None

def extract_isbn_from_url(url: str) -> str:
    """Extract ISBN from URL."""
    # Look for ISBN patterns in URL
    isbn_pattern = r'(?:isbn[-/]?|978[-/]?|10[-/]?)(\d{9,13})'
    match = re.search(isbn_pattern, url.lower())
    if match:
        return match.group(1).replace('-', '').replace('/', '')
    return None
