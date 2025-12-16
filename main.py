import sys
import os

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

if __name__ == "__main__":
    

    latex_text = r"""
    Normal URL in the text: https://doi.org/10.1038/s41586-020-2649-2.
    https://www.nature.com/articles/s41586-020-2649-2
    https://arxiv.org/abs/2102.06714
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
