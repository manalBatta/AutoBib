import requests
from urllib.parse import quote

def fetch_crossref(doi: str):
    headers = {"Accept": "application/json"}
    encoded_doi = quote(doi, safe="")
    url = f"https://api.crossref.org/works/{encoded_doi}"
    print(f"[crossref] Requesting DOI={doi} url={url}")
    try:
        r = requests.get(url, headers=headers, timeout=10)
    except requests.RequestException as exc:
        print(f"[crossref] Request error for DOI={doi}: {exc}")
        return None

    if r.status_code == 200:
        try:
            body = r.json()
            if "message" not in body:
                print(f"[crossref] 200 response missing 'message' key for DOI={doi}")
                return None
            return body["message"]
        except ValueError as exc:
            print(f"[crossref] Invalid JSON for DOI={doi}: {exc}")
            return None

    print(f"[crossref] Non-200 status={r.status_code} DOI={doi} response={r.text[:300]}")
    return None
