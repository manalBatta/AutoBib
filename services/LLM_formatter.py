# services/LLM_formatter.py
import re
from utils.serper import enrich_metadata


def _slugify(text: str, max_len: int = 10) -> str:
    """Convert text to lowercase alphanumeric slug suitable for BibTeX key."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text[:max_len] or "paper"


def generate_bibtex_key(metadata: dict, suffix: str = "") -> str:
    """
    Generate BibTeX key using author-year-title convention.
    Enhanced to handle different source types appropriately.
    
    Example: Ray2025NearFutureMev
    """
    entry_type = metadata.get("type", "article")
    authors = metadata.get("author", [])
    year = metadata.get("year", "XXXX")
    title = metadata.get("title", "")

    # Handle different author formats for different source types
    if entry_type == "software" and authors:
        # For software, use repository name or first author
        first_author_last = metadata.get("title", "").split()[-1][:8].lower()
    elif entry_type == "techreport" and authors:
        # For technical reports, use organization name
        first_author_last = authors[0].split()[-1]
    elif entry_type == "book" and authors:
        # For books, use first author's last name
        first_author_last = authors[0].split()[-1]
    elif authors:
        first_author_last = authors[0].split()[-1]
    else:
        first_author_last = "Anon"

    title_slug = _slugify(title)

    return f"{first_author_last}{year}{title_slug}{suffix}"


def format_as_bibtex(
    metadata: dict,
    style: str = "bibtex",
    use_mock: bool = True,
    key_suffix: str = ""
) -> str:
    """
    Format metadata dict as a BibTeX entry (Serper enriches metadata when use_mock=False).
    Enhanced to handle different entry types appropriately.
    Only includes non-empty fields for professional appearance.
    """
    bibtex_key = generate_bibtex_key(metadata, suffix=key_suffix)
    entry_type = metadata.get("type", "article")
    
    # Map our internal types to proper BibTeX entry types
    bibtex_type_mapping = {
        "article": "article",
        "book": "book", 
        "software": "software",
        "techreport": "techreport",
        "misc": "misc",
        "inproceedings": "inproceedings"
    }
    
    bibtex_entry_type = bibtex_type_mapping.get(entry_type, "misc")

    def format_field(name: str, value: str) -> str:
        """Helper to format a field only if value is non-empty"""
        if value and str(value).strip() and str(value).lower() != 'none':
            return f"  {name}={{{value}}},\n"
        return ""

    if not use_mock:
        metadata = enrich_metadata(metadata)

    # Build BibTeX from metadata fields
    if entry_type == "book":
        fields = [
            format_field("title", metadata.get('title', '')),
            format_field("author", ' and '.join(metadata.get('author', []))),
            format_field("year", metadata.get('year', '')),
            format_field("publisher", metadata.get('publisher', '')),
            format_field("isbn", metadata.get('isbn', '')),
            format_field("pages", metadata.get('pages', '')),
            format_field("edition", metadata.get('edition', '')),
            format_field("address", metadata.get('address', ''))
        ]
        return "@book{" + bibtex_key + ",\n" + ''.join(fields)

    elif entry_type == "software":
        fields = [
            format_field("title", metadata.get('title', '')),
            format_field("author", ' and '.join(metadata.get('author', []))),
            format_field("year", metadata.get('year', '')),
            format_field("publisher", metadata.get('publisher', 'GitHub')),
            format_field("url", metadata.get('URL', '')),
            format_field("version", metadata.get('version', '')),
            format_field("license", metadata.get('license', '')),
            format_field("language", metadata.get('language', ''))
        ]
        return "@software{" + bibtex_key + ",\n" + ''.join(fields)

    elif entry_type == "techreport":
        fields = [
            format_field("title", metadata.get('title', '')),
            format_field("author", ' and '.join(metadata.get('author', []))),
            format_field("year", metadata.get('year', '')),
            format_field("institution", metadata.get('publisher', '')),
            format_field("number", metadata.get('number', '')),
            format_field("type", metadata.get('type', '')),
            format_field("url", metadata.get('URL', ''))
        ]
        return "@techreport{" + bibtex_key + ",\n" + ''.join(fields)

    elif entry_type == "misc":
        fields = [
            format_field("title", metadata.get('title', '')),
            format_field("author", ' and '.join(metadata.get('author', []))),
            format_field("year", metadata.get('year', '')),
            format_field("howpublished", metadata.get('publisher', '')),
            format_field("url", metadata.get('URL', '')),
            format_field("version", metadata.get('version', '')),
            format_field("note", metadata.get('description', ''))
        ]
        return "@misc{" + bibtex_key + ",\n" + ''.join(fields)

    else:
        fields = [
            format_field("title", metadata.get('title', '')),
            format_field("author", ' and '.join(metadata.get('author', []))),
            format_field("year", metadata.get('year', '')),
            format_field("journal", metadata.get('container-title', '')),
            format_field("volume", metadata.get('volume', '')),
            format_field("number", metadata.get('issue', '')),
            format_field("pages", metadata.get('page', '')),
            format_field("doi", metadata.get('doi', '')),
            format_field("url", metadata.get('URL', ''))
        ]
        return "@" + bibtex_entry_type + "{" + bibtex_key + ",\n" + ''.join(fields)
