import re

def resolve_doi(url: str) -> str | None:
    m = re.search(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', url, re.I)
    return m.group(0) if m else None
