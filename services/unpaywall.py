import requests

def fetch_unpaywall(url: str):
    api = f"https://api.unpaywall.org/v2/{url}?email=YOUR_EMAIL@domain.com"
    r = requests.get(api, timeout=6)
    if r.status_code == 200:
        return r.json()
    return None
