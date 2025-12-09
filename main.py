import sys
import os
from utils.cache import load_from_cache, dump_to_cache
from retriever.metadata_retriever import retrieve_metadata
from services.LLM_formatter import format_as_bibtex
from validation.bibtex_validation import validate_bibtex
import openai
from services.extractURL import extract_urls

# Optional: set API key if you want real OpenAI calls
# openai.api_key = os.getenv("OPENAI_API_KEY")


def bibtex_from_url(url: str, use_mock: bool = True) -> str:
    # Check cache first
    cached = load_from_cache(url)
    if cached:
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
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": fix_prompt}],
                temperature=0,
                max_tokens=200,
            ).choices[0].message.content.strip()

            if validate_bibtex(fix):
                bib = fix

    # Save to cache
    dump_to_cache(url, {"metadata": md, "bibtex": bib})
    return bib

if __name__ == "__main__":
    

    latex_text = r"""
    Normal URL in the text: https://doi.org/10.1038/s41586-020-2649-2.
    Ignore this: \url{https://inside-url.com/page}.
    Ignore href: \href{https://inside-link.com}{Click here}.
    Ignore macro: \newcommand{\myurl}{https://macro-url.com}.
    Another raw URL: www.testsite.org/path?ref=123.
    Multi-line URL: https://longsite.com/very/long/
    path/to/page
    """
    print("Extracted URLs:")
    for u in extract_urls(latex_text):
          print(" -", u)
          print(bibtex_from_url(u, use_mock=True))



   # print(extract_urls(sample_text))
   
    if len(sys.argv) == 1:
        print("Usage: python main.py <url>")
        sys.exit(1)

    # Use mock=True to avoid OpenAI API calls and quota issues
