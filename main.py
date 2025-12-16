import sys
import os
import re

import openai

from config.settings import OPENAI_API_KEY, OPENAI_MODEL
from utils.cache import load_from_cache, dump_to_cache
from retriever.metadata_retriever import retrieve_metadata
from services.LLM_formatter import format_as_bibtex
from validation.bibtex_validation import validate_bibtex
from services.extractURL import extract_urls

# Configure OpenAI with key from settings (only needed when use_mock=False)
openai.api_key = OPENAI_API_KEY



def bibtex_from_url(url: str, use_mock: bool = True) -> str:
    # Check cache first
    cached = load_from_cache(url)
    if cached:
        print("Cached bibtex found")
        return cached["bibtex"]

    # Retrieve metadata
    md = retrieve_metadata(url)

    # Format BibTeX
    bib = format_as_bibtex(md, use_mock=use_mock)

    # Validate and optionally fix
    if not validate_bibtex(bib):
        if use_mock:
            # Skip fixing for mock
            pass
        else:
            fix_prompt = f"Fix syntax errors in this BibTeX entry:\n\n{bib}"
            fix = openai.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": fix_prompt}],
                temperature=0,
                max_tokens=200,
            ).choices[0].message.content.strip()

            if validate_bibtex(fix):
                bib = fix

    # Save to cache
    #dump_to_cache(url, {"metadata": md, "bibtex": bib})
    return bib


_BIB_KEY_RE = re.compile(r"@\w+\{([^,]+),")


def _extract_bibtex_key(bibtex: str) -> str | None:
    """Extract the BibTeX key from a BibTeX entry string."""
    m = _BIB_KEY_RE.search(bibtex)
    return m.group(1).strip() if m else None

if __name__ == "__main__":
    # Expect a path to a .tex file as the first argument
    if len(sys.argv) < 2:
        print("Usage: python main.py <path-to-file.tex>")
        sys.exit(1)

    tex_path = sys.argv[1]

    if not os.path.isfile(tex_path):
        print(f"Error: file not found: {tex_path}")
        sys.exit(1)

    with open(tex_path, "r", encoding="utf-8") as f:
        latex_text = f.read()

    # Derive output .bib file path from the .tex path
    base, _ = os.path.splitext(tex_path)
    bib_path = base + ".bib"

    print("Extracted URLs:")
    urls = extract_urls(latex_text)

    if not urls:
        print("No URLs found in the provided .tex file.")
        sys.exit(0)

    url_to_key: dict[str, str] = {}

    # Write all BibTeX entries to a .bib file (overwrite on each run)
    with open(bib_path, "w", encoding="utf-8") as bib_file:
        for u in urls:
            print(" -", u)
            bib = bibtex_from_url(u, use_mock=True)
            print(bib)
            bib_file.write(bib)
            bib_file.write("\n\n")

            key = _extract_bibtex_key(bib)
            if key:
                url_to_key[u] = key

    # Replace URLs in LaTeX text with ~\Cite{key}
    for u, key in url_to_key.items():
        latex_text = latex_text.replace(u, f"\\cite{{{key}}}")

    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(latex_text)

    print(f"\nAll BibTeX entries written to: {bib_path}")
    print(f"Updated LaTeX file with \\Cite{{...}} commands: {tex_path}")
