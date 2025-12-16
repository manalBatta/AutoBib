import re
from services.doi_resolver import resolve_doi
from services.crossref import fetch_crossref
from services.arxiv import fetch_arxiv
from services.unpaywall import fetch_unpaywall
from services.pdf_extractor import extract_pdf_metadata

def retrieve_metadata(url: str) -> dict:

    doi = resolve_doi(url)
    if doi:
        msg = fetch_crossref(doi)
        if msg:
            return {
                "title": msg.get("title", [""])[0],
                "author": [f"{a.get('given','')} {a.get('family','')}".strip()
                           for a in msg.get("author", [])],
                "year": msg.get("published-print", msg.get("published-online", {}))
                           .get("date-parts", [[None]])[0][0],
                "doi": doi,
                "URL": url,
                "type": "article",
                "container-title": msg.get("container-title", [""])[0],
                "volume": msg.get("volume"),
                "issue": msg.get("issue"),
                "page": msg.get("page")
            }
        
    m = re.search(r'arxiv\.org/abs/([0-9\.]+)', url)
    if m:
        rec = fetch_arxiv(m.group(1))
        if rec:
            return rec
        

    oa = fetch_unpaywall(url)
    if oa and oa.get("best_oa_location", {}).get("url"):
        print("Unpaywall metadata found for ", url)
        pdf_url = oa["best_oa_location"]["url"]
        pdf_md = extract_pdf_metadata(pdf_url)
        if pdf_md:
            pdf_md.update({"URL": url, "type": "article"})
            return pdf_md
    print("No metadata found for ", url)
    return {
        "title": "UNKNOWN",
        "author": ["UNKNOWN"],
        "year": None,
        "URL": url,
        "type": "misc"
    }
