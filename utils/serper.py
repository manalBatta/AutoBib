import re

import requests

from config.settings import SERPER_API_KEY

SEARCH_URL = "https://google.serper.dev/search"
SCHOLAR_URL = "https://google.serper.dev/scholar"


def _post(url: str, query: str) -> dict:
    response = requests.post(
        url,
        headers={
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json",
        },
        json={"q": query},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def search(query: str) -> dict:
    return _post(SEARCH_URL, query)


def scholar_search(query: str) -> dict:
    return _post(SCHOLAR_URL, query)


def _parse_publication_info(info) -> dict:
    """Parse Serper publicationInfo string, e.g. 'A Author - Journal, 2020 - site.com'."""
    if isinstance(info, dict):
        out = {}
        summary = info.get("summary", "")
        authors = info.get("authors") or []
        if authors:
            out["author"] = [
                a.get("name", str(a)) if isinstance(a, dict) else str(a) for a in authors
            ]
        if summary:
            info = summary
        else:
            return out

    if not info or not isinstance(info, str):
        return {}

    out = {}
    year_match = re.search(r"\b(19|20)\d{2}\b", info)
    if year_match:
        out["year"] = year_match.group(0)

    parts = [p.strip() for p in info.split(" - ")]
    if parts:
        author_part = parts[0]
        if author_part and not re.match(r"^https?://", author_part, re.I):
            names = [n.strip() for n in re.split(r",|\band\b", author_part) if n.strip()]
            if names:
                out["author"] = names
    if len(parts) > 1:
        venue = parts[1].split(",")[0].strip()
        if venue and not re.match(r"^\d{4}$", venue):
            out["container-title"] = venue

    return out


def enrich_metadata(metadata: dict) -> dict:
    """Use Serper Scholar (fallback: web search) to fill missing citation fields."""
    title = metadata.get("title", "")
    url = metadata.get("URL", "")
    authors = metadata.get("author") or []
    first_author = authors[0] if authors else ""

    query = " ".join(p for p in [title, first_author, url] if p).strip()
    if not query:
        return metadata

    try:
        data = scholar_search(query)
    except Exception:
        data = search(query)

    organic = data.get("organic") or []
    if not organic:
        return metadata

    hit = organic[0]
    enriched = dict(metadata)

    if hit.get("title"):
        enriched["title"] = hit["title"]
    if hit.get("link"):
        enriched["URL"] = enriched.get("URL") or hit["link"]
    if hit.get("year"):
        enriched["year"] = str(hit["year"])

    pub = hit.get("publicationInfo")
    if pub:
        parsed = _parse_publication_info(pub)
        for key, value in parsed.items():
            if value and not enriched.get(key):
                enriched[key] = value

    return enriched
