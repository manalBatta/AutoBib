import time

import feedparser
import requests

ARXIV_USER_AGENT = "AutoBib/1.0 (mailto:autobib@example.com)"


def fetch_arxiv(arxiv_id: str, max_retries: int = 3) -> dict | None:
    url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
    headers = {"User-Agent": ARXIV_USER_AGENT}

    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            if r.status_code != 200:
                return None

            feed = feedparser.parse(r.text)
            if feed.entries:
                e = feed.entries[0]
                return {
                    "title": e.title,
                    "author": [a["name"] for a in e.authors],
                    "published": e.published,
                    "doi": e.get("doi"),
                    "URL": e.id,
                    "type": "article",
                    "container-title": "arXiv preprint",
                }
            return None
        except requests.RequestException:
            if attempt + 1 < max_retries:
                time.sleep(2 ** attempt)
            continue

    return None
