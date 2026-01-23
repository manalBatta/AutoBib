import sys
import os
import re
import time
from tqdm import tqdm  # pip install tqdm

# Imports from your project structure
from config.settings import OPENAI_API_KEY, OPENAI_MODEL
from utils.cache import load_from_cache, dump_to_cache
from retriever.metadata_retriever import retrieve_metadata
from services.LLM_formatter import format_as_bibtex
from validation.bibtex_validation import validate_bibtex
from services.extractURL import extract_urls
import openai

openai.api_key = OPENAI_API_KEY

# ==========================================
# Helper Functions
# ==========================================

def bibtex_from_url(url: str, use_mock: bool = True) -> str | None:
    # Check cache first
    cached = load_from_cache(url)
    if cached:
        return cached["bibtex"]

    # Retrieve metadata
    md = retrieve_metadata(url)
    if md is None:
        return None

    # Format BibTeX
    bib = format_as_bibtex(md, use_mock=use_mock)

    # Validate and optionally fix
    if not validate_bibtex(bib):
        if use_mock:
            pass
        else:
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
            except:
                pass

    # Save to cache
    # dump_to_cache(url, {"metadata": md, "bibtex": bib})
    return bib


_BIB_KEY_RE = re.compile(r"@\w+\{([^,]+),")

def _extract_bibtex_key(bibtex: str) -> str | None:
    m = _BIB_KEY_RE.search(bibtex)
    return m.group(1).strip() if m else None

# ==========================================
# Main Execution
# ==========================================

if __name__ == "__main__":
    
    # 1. Start the Timer
    start_time = time.time()

    # Handle Arguments
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

    # Derive output paths
    base, _ = os.path.splitext(tex_path)
    bib_path = base + ".bib"
    
    # Extract URLs
    urls = extract_urls(latex_text)
    
    if not urls:
        print("No URLs found in the provided .tex file.")
        sys.exit(0)

    print(f"Found {len(urls)} URLs. Starting processing...\n")

    url_to_key: dict[str, str] = {}
    success_count = 0
    fail_count = 0

    # Open Bib file to write results
    with open(bib_path, "w", encoding="utf-8") as bib_file:
        
        # 2. Loop through URLs with a Progress Bar
        for u in tqdm(urls, desc="Fetching Citations", unit="link"):
            
            try:
                # --- SAFELY TRY TO GET BIBTEX ---
                # Change use_mock=False if you want real data from OpenAI
                bib = bibtex_from_url(u, use_mock=True) 
                
                if bib is None:
                    # If metadata retrieval returned None (but didn't crash)
                    fail_count += 1
                    continue
                
                # Success! Write to file
                success_count += 1
                bib_file.write(bib)
                bib_file.write("\n\n")

                key = _extract_bibtex_key(bib)
                if key:
                    url_to_key[u] = key
                    
            except Exception as e:
                # --- CRASH HANDLER ---
                # If a timeout or internet error happens, catch it here
                # So the loop continues to the next link
                # Using tqdm.write prevents the progress bar from breaking
                tqdm.write(f"\n[Error] Failed to process {u}: {e}")
                fail_count += 1

    # Replace URLs in text
    for u, key in url_to_key.items():
        latex_text = latex_text.replace(u, f"\\cite{{{key}}}")

    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(latex_text)

    # 3. Stop the Timer & Calculate Analysis
    end_time = time.time()
    total_time = end_time - start_time
    
    # Assumptions for Manual Labor
    MANUAL_TIME_PER_LINK_SEC = 120.0  # 2 minutes per link
    manual_total_time = len(urls) * MANUAL_TIME_PER_LINK_SEC
    time_saved_sec = manual_total_time - total_time
    time_saved_min = time_saved_sec / 60.0
    speedup_factor = manual_total_time / total_time if total_time > 0 else 0

    # 4. Print the Performance Report
    print("\n" + "="*40)
    print("       PERFORMANCE ANALYSIS REPORT       ")
    print("="*40)
    print(f"Total Links Processed:   {len(urls)}")
    print(f"Successful Extractions:  {success_count}")
    print(f"Failed Extractions:      {fail_count}")
    print("-" * 40)
    print(f"Automated Runtime:       {total_time:.2f} seconds")
    print(f"Average Time per Link:   {total_time/len(urls):.2f} seconds")
    print("-" * 40)
    print(f"Est. Manual Time (2m/link): {manual_total_time/60:.1f} minutes")
    print(f"TIME SAVED:              {time_saved_min:.1f} minutes")
    print(f"EFFICIENCY GAIN:         {speedup_factor:.1f}x Faster")
    print("="*40)
    print(f"Results saved to: {bib_path}")