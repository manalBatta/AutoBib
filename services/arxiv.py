import time

import feedparser
import requests

ARXIV_USER_AGENT = "AutoBib/1.0 (mailto:autobib@example.com)"


def fetch_arxiv(arxiv_id: str, max_retries: int = 3) -> dict | None:
    url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
    headers = {"User-Agent": ARXIV_USER_AGENT}

    for attempt in range(max_retries):
        try:
            print(f"[arxiv] Attempt {attempt + 1}/{max_retries} id={arxiv_id} url={url}")
            r = requests.get(url, headers=headers, timeout=50)
            if r.status_code == 429:
                wait_sec = 2 ** attempt
                print(f"[arxiv] Rate limited (429) for id={arxiv_id}. Retrying in {wait_sec}s")
                time.sleep(2 ** attempt)
                continue
            if r.status_code != 200:
                print(f"[arxiv] Non-200 status={r.status_code} for id={arxiv_id} response={r.text[:300]}")
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
            print(
                f"[arxiv] Parsed feed but no entries for id={arxiv_id}. "
                f"bozo={getattr(feed, 'bozo', None)} snippet={r.text[:300]}"
            )
            return None
        except requests.RequestException as exc:
            print(f"[arxiv] Request exception for id={arxiv_id} attempt={attempt + 1}: {exc}")
            if attempt + 1 < max_retries:
                time.sleep(2 ** attempt)
            continue

    print(f"[arxiv] Exhausted retries for id={arxiv_id}")
    return None
