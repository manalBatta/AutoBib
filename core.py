import logging
import os
import re
import time
from typing import Callable

import openai

from config.settings import OPENAI_API_KEY, OPENAI_MODEL
from retriever.metadata_retriever import retrieve_metadata
from services.LLM_formatter import format_as_bibtex
from services.extractURL import extract_urls
from utils.cache import load_from_cache
from validation.bibtex_validation import validate_bibtex

logger = logging.getLogger(__name__)
openai.api_key = OPENAI_API_KEY

_BIB_KEY_RE = re.compile(r"@\w+\{([^,]+),")
_REQUEST_DELAY_SEC = float(os.getenv("REQUEST_DELAY_SEC", "0.4"))


class NoUrlsFoundError(Exception):
    """Raised when the LaTeX input contains no extractable URLs."""


def _use_mock_default() -> bool:
    env = os.getenv("USE_MOCK", "").lower()
    if env in ("0", "false", "no"):
        return False
    if env in ("1", "true", "yes"):
        return True
    # Default to mock formatting (no OpenAI call) unless explicitly disabled.
    return True


def bibtex_from_url(url: str, use_mock: bool | None = None) -> str | None:
    if use_mock is None:
        use_mock = _use_mock_default()

    cached = load_from_cache(url)
    if cached:
        return cached["bibtex"]

    md = retrieve_metadata(url)
    if md is None:
        return None

    bib = _format_bibtex_with_fallback(md, use_mock=use_mock)
    if not bib:
        return None

    if not validate_bibtex(bib) and not use_mock:
        try:
            fix_prompt = f"Fix syntax errors in this BibTeX entry:\n\n{bib}"
            fix = openai.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": fix_prompt}],
                temperature=0,
                max_tokens=200,
            ).choices[0].message.content.strip()

            if validate_bibtex(fix):
                bib = fix
        except Exception as exc:
            logger.warning("BibTeX fix via OpenAI failed for %s: %s", url, exc)

    return bib


def _format_bibtex_with_fallback(metadata: dict, use_mock: bool) -> str | None:
    if use_mock:
        return format_as_bibtex(metadata, use_mock=True)

    try:
        return format_as_bibtex(metadata, use_mock=False)
    except Exception as exc:
        logger.warning(
            "OpenAI BibTeX formatting failed (%s), falling back to template formatter.",
            exc,
        )
        return format_as_bibtex(metadata, use_mock=True)


def _extract_bibtex_key(bibtex: str) -> str | None:
    m = _BIB_KEY_RE.search(bibtex)
    return m.group(1).strip() if m else None


def process_latex(
    latex_text: str,
    use_mock: bool | None = None,
    on_url_processed: Callable[[int, int, str], None] | None = None,
) -> dict:
    """
    Process LaTeX text: fetch BibTeX for URLs and replace them with \\cite{key}.

    Returns:
        {
            "edited_tex": str,
            "bib": str,
            "stats": {
                "urls_found": int,
                "success": int,
                "failed": int,
                "elapsed_seconds": float,
            },
        }
    """
    if use_mock is None:
        use_mock = _use_mock_default()

    start_time = time.time()
    urls = extract_urls(latex_text)

    if not urls:
        raise NoUrlsFoundError("No URLs found in the provided .tex file.")

    url_to_key: dict[str, str] = {}
    bib_entries: list[str] = []
    success_count = 0
    fail_count = 0
    total = len(urls)

    for index, url in enumerate(urls, start=1):
        try:
            bib = bibtex_from_url(url, use_mock=use_mock)
            if bib is None:
                fail_count += 1
                logger.warning("No BibTeX produced for %s", url)
            else:
                success_count += 1
                bib_entries.append(bib)
                key = _extract_bibtex_key(bib)
                if key:
                    url_to_key[url] = key
                else:
                    logger.warning("Could not parse BibTeX key for %s", url)
        except Exception as exc:
            fail_count += 1
            logger.exception("Failed to process %s: %s", url, exc)

        if on_url_processed:
            on_url_processed(index, total, url)

        if index < total and _REQUEST_DELAY_SEC > 0:
            time.sleep(_REQUEST_DELAY_SEC)

    edited_tex = latex_text
    for url, key in url_to_key.items():
        edited_tex = edited_tex.replace(url, f"\\cite{{{key}}}")

    elapsed = time.time() - start_time

    return {
        "edited_tex": edited_tex,
        "bib": "\n\n".join(bib_entries) + ("\n" if bib_entries else ""),
        "stats": {
            "urls_found": len(urls),
            "success": success_count,
            "failed": fail_count,
            "elapsed_seconds": round(elapsed, 2),
        },
    }
