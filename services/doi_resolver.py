import re

import requests
from bs4 import BeautifulSoup

# Matches common DOI shapes
DOI_REGEX = re.compile(r"10\.\d{4,9}/[^\s\"'>]+", re.I)


def resolve_doi(url: str) -> str | None:
    # 1) Check DOI in the URL itself
    m = DOI_REGEX.search(url)
    if m:
        return m.group(0)

    # 2) Scrape the page for a DOI
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"resolve_doi: fetch failed ({resp.status_code}) for {url}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Meta tags commonly used to store DOIs
        meta_names = {"citation_doi", "dc.identifier", "DC.identifier", "prism.doi", "prism.doi", "article:doi"}
        for tag in soup.find_all("meta"):
            name = tag.get("name") or tag.get("property") or ""
            if name in meta_names:
                content = tag.get("content") or ""
                m = DOI_REGEX.search(content)
                if m:
                    return _clean_doi(m.group(0))

            # If not a known name, still scan the content for a DOI
            content = tag.get("content") or ""
            m = DOI_REGEX.search(content)
            if m:
                return _clean_doi(m.group(0))

        # Links occasionally carry the DOI
        for tag in soup.find_all("link"):
            href = tag.get("href") or ""
            m = DOI_REGEX.search(href)
            if m:
                return _clean_doi(m.group(0))

        # Fallback: search the full page text
        m = DOI_REGEX.search(resp.text)
        if m:
            return _clean_doi(m.group(0))
    except Exception as exc:
        print(f"resolve_doi: error for {url}: {exc}")
        return None

    return None


def _clean_doi(raw: str) -> str:
    raw = raw.strip()
    if "doi.org/" in raw:
        raw = raw.split("doi.org/")[-1]
    return raw