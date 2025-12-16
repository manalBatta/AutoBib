# services/LLM_formatter.py
import json
import openai
import re
from config.settings import OPENAI_API_KEY, OPENAI_MODEL

openai.api_key = OPENAI_API_KEY


def _slugify(text: str, max_len: int = 10) -> str:
    """Convert text to lowercase alphanumeric slug suitable for BibTeX key."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text[:max_len] or "paper"


def generate_bibtex_key(metadata: dict, suffix: str = "") -> str:
    """
    Generate BibTeX key using author-year-title convention.
    
    Example: Ray2025NearFutureMev
    """
    authors = metadata.get("author", [])
    year = metadata.get("year", "XXXX")
    title = metadata.get("title", "")

    if authors:
        first_author_last = authors[0].split()[-1]
    else:
        first_author_last = "Anon"

    title_slug = _slugify(title)

    return f"{first_author_last}{year}{title_slug}{suffix}"


def format_as_bibtex(
    metadata: dict,
    style: str = "bibtex",
    model: str = OPENAI_MODEL,
    use_mock: bool = True,
    key_suffix: str = ""
) -> str:
    """
    Format metadata dict as a BibTeX entry using OpenAI LLM.
    Generates a BibTeX key following the author-year-title convention.
    """
    bibtex_key = generate_bibtex_key(metadata, suffix=key_suffix)
    entry_type = metadata.get("type", "article")

    if use_mock:
        return f"""@{entry_type}{{{bibtex_key},
  title={{ {metadata.get('title','UNKNOWN')} }},
  author={{ {' and '.join(metadata.get('author',[]))} }},
  year={{ {metadata.get('year','')} }}
}}"""

    prompt = f"""You are a citation formatter.
Output a single BibTeX entry of type @{entry_type}.
Use the citation key: {bibtex_key}.
Include all non-empty fields only.

Metadata:
```json
{json.dumps(metadata, indent=2)}
```"""

    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=200,
    )

    return response.choices[0].message.content.strip()
