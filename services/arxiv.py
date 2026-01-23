import requests
import feedparser

def fetch_arxiv(arxiv_id: str):
    r = requests.get(f"http://export.arxiv.org/api/query?id_list={arxiv_id}", timeout=30)
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
            "container-title": "arXiv preprint"
        }
    return None
