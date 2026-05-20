import re
from services.doi_resolver import resolve_doi
from services.crossref import fetch_crossref
from services.arxiv import fetch_arxiv
from services.unpaywall import fetch_unpaywall
from services.pdf_extractor import extract_pdf_metadata
from services.google_books import fetch_google_books, extract_isbn_from_url
from services.github_api import fetch_github_repo, is_github_url
from services.standards_parser import fetch_ieee_standard, fetch_rfc_document, fetch_w3c_spec, fetch_documentation, is_standard_url

def retrieve_metadata(url: str) -> dict:

    # Check for GitHub repositories first
    if is_github_url(url):
        print("GitHub repository detected for ", url)
        repo_data = fetch_github_repo(url)
        if repo_data:
            print("GitHub metadata found for ", url)
            return repo_data

    # Check for technical standards and documentation
    standard_type = is_standard_url(url)
    if standard_type:
        print(f"{standard_type.upper()} standard/documentation detected for ", url)
        if standard_type == 'ieee':
            data = fetch_ieee_standard(url)
        elif standard_type == 'rfc':
            data = fetch_rfc_document(url)
        elif standard_type == 'w3c':
            data = fetch_w3c_spec(url)
        elif standard_type == 'documentation':
            data = fetch_documentation(url)
        else:
            data = None
        
        if data:
            print(f"{standard_type.upper()} metadata found for ", url)
            return data

    # Check for books (ISBN in URL or common book publisher patterns)
    isbn = extract_isbn_from_url(url)
    book_publishers = ['mhprofessional.com', 'pearson.com', 'addison-wesley.com', 'oreilly.com', 'apress.com', 'springer.com']
    if isbn or any(publisher in url.lower() for publisher in book_publishers):
        print("Book detected for ", url)
        book_data = fetch_google_books(isbn=isbn)
        if book_data:
            print("Book metadata found for ", url)
            return book_data

    doi = resolve_doi(url)
    print("DOI for ", url, doi)
    if doi:
        print("DOI found for ", url)
        msg = fetch_crossref(doi)
        if msg:
            print("Crossref metadata found for ", url)
            return {
                "title": msg.get("title", [""])[0] if msg.get("title") else "",
                "author": [f"{a.get('given','')} {a.get('family','')}".strip()
                           for a in msg.get("author", [])],
                "year": msg.get("published-print", msg.get("published-online", {}))
                           .get("date-parts", [[None]])[0][0],
                "doi": doi,
                "URL": url,
                "type": "article",
                "container-title": msg.get("container-title", [""])[0] if msg.get("container-title") else "",
                "volume": msg.get("volume"),
                "issue": msg.get("issue"),
                "page": msg.get("page")
            }
        else:
            print("No crossref metadata found for ", url)
    # Try to match arXiv URLs of the form .../abs/<id> or .../pdf/<id>.pdf
    m = re.search(r'arxiv\.org/(?:abs|pdf)/([0-9]+\.[0-9]+)(?:\.pdf)?', url)
    if m:
        print("Arxiv ID found for ", url)
        rec = fetch_arxiv(m.group(1))
        if rec:
            print("Arxiv metadata found for ", url)
            # Reformat the rec dictionary to match the expected bibtex format
            new_rec = {
                "title": rec.get("title", "UNKNOWN"),
                "author": rec.get("author", ["UNKNOWN"]),
                "year": None,
                "URL": rec.get("URL", url),
                "type": rec.get("type", "article"),
                "container-title": rec.get("container-title", ""),
                "doi": rec.get("doi")
            }
            # Try to extract the year from the 'published' field if available
            published = rec.get("published")
            if published:
                # Expecting format like '2021-02-26T19:04:58Z'
                m = re.match(r"(\d{4})", published)
                if m:
                    new_rec["year"] = int(m.group(1))
            rec = new_rec
            return rec
        else:
            print("No arxiv metadata found for ", url)

    oa = fetch_unpaywall(url)
    if oa and oa.get("best_oa_location", {}).get("url"):
        print("Unpaywall metadata found for ", url)
        pdf_url = oa["best_oa_location"]["url"]
        pdf_md = extract_pdf_metadata(pdf_url)
        if pdf_md:
            pdf_md.update({"URL": url, "type": "article"})
            return pdf_md
    print("No metadata found for ", url)
    return None