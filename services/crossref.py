import requests

def fetch_crossref(doi: str):
    headers = {"Accept": "application/json"}
    r = requests.get(f"https://api.crossref.org/works/{doi}", headers=headers, timeout=10)
    if r.status_code == 200:
        return r.json()["message"]
    return None
