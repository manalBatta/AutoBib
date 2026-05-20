import logging
import os
import re
import sys
import time

from tqdm import tqdm

from retriever.metadata_retriever import retrieve_metadata
from services.LLM_formatter import format_as_bibtex
from services.extractURL import extract_urls
from utils.cache import load_from_cache

logger = logging.getLogger(__name__)

# ==========================================
# Helper Functions
# ==========================================


class NoUrlsFoundError(Exception):
    """Raised when the LaTeX input contains no extractable URLs."""


def bibtex_from_url(url: str, use_mock: bool = True) -> str | None:
    cached = load_from_cache(url)
    if cached:
        return cached["bibtex"]

    md = retrieve_metadata(url)
    if md is None:
        return None

    bib = format_as_bibtex(md, use_mock=use_mock)

    # dump_to_cache(url, {"metadata": md, "bibtex": bib})
    return bib


_BIB_KEY_RE = re.compile(r"@\w+\{([^,]+),")


def _extract_bibtex_key(bibtex: str) -> str | None:
    m = _BIB_KEY_RE.search(bibtex)
    return m.group(1).strip() if m else None


def process_latex(latex_text: str) -> dict:
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
    start_time = time.time()
    urls = extract_urls(latex_text)

    if not urls:
        raise NoUrlsFoundError("No URLs found in the provided .tex file.")

    url_to_key: dict[str, str] = {}
    bib_entries: list[str] = []
    success_count = 0
    fail_count = 0

    use_tqdm = sys.stdout.isatty()
    url_iter = tqdm(urls, desc="Fetching Citations", unit="link") if use_tqdm else urls

    for u in url_iter:
        try:
            bib = bibtex_from_url(u, use_mock=False)

            if bib is None:
                fail_count += 1
                continue

            success_count += 1
            bib_entries.append(bib)

            key = _extract_bibtex_key(bib)
            if key:
                url_to_key[u] = key

        except Exception as e:
            if use_tqdm:
                tqdm.write(f"\n[Error] Failed to process {u}: {e}")
            else:
                logger.exception("Failed to process %s: %s", u, e)
            fail_count += 1

    edited_tex = latex_text
    for u, key in url_to_key.items():
        edited_tex = edited_tex.replace(u, f"\\cite{{{key}}}")

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


# ==========================================
# CLI
# ==========================================

if __name__ == "__main__":
    start_time = time.time()

    if len(sys.argv) < 2:
        print("Usage: python main.py <path-to-file.tex>")
        sys.exit(1)

    tex_path = sys.argv[1]

    if not os.path.isfile(tex_path):
        print(f"Error: file not found: {tex_path}")
        sys.exit(1)

    print(f"Reading file: {tex_path}...")
    with open(tex_path, "r", encoding="utf-8") as f:
        latex_text = f.read()

    base, _ = os.path.splitext(tex_path)
    bib_path = base + ".bib"

    try:
        result = process_latex(latex_text)
    except NoUrlsFoundError:
        print("No URLs found in the provided .tex file.")
        sys.exit(0)

    urls_count = result["stats"]["urls_found"]
    success_count = result["stats"]["success"]
    fail_count = result["stats"]["failed"]

    print(f"Found {urls_count} URLs. Starting processing...\n")

    with open(bib_path, "w", encoding="utf-8") as bib_file:
        bib_file.write(result["bib"])

    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(result["edited_tex"])

    total_time = time.time() - start_time

    MANUAL_TIME_PER_LINK_SEC = 120.0
    manual_total_time = urls_count * MANUAL_TIME_PER_LINK_SEC
    time_saved_sec = manual_total_time - total_time
    time_saved_min = time_saved_sec / 60.0
    speedup_factor = manual_total_time / total_time if total_time > 0 else 0

    print("\n" + "=" * 40)
    print("       PERFORMANCE ANALYSIS REPORT       ")
    print("=" * 40)
    print(f"Total Links Processed:   {urls_count}")
    print(f"Successful Extractions:  {success_count}")
    print(f"Failed Extractions:      {fail_count}")
    print("-" * 40)
    print(f"Automated Runtime:       {total_time:.2f} seconds")
    print(f"Average Time per Link:   {total_time / urls_count:.2f} seconds")
    print("-" * 40)
    print(f"Est. Manual Time (2m/link): {manual_total_time / 60:.1f} minutes")
    print(f"TIME SAVED:              {time_saved_min:.1f} minutes")
    print(f"EFFICIENCY GAIN:         {speedup_factor:.1f}x Faster")
    print("=" * 40)
    print(f"Results saved to: {bib_path}")
