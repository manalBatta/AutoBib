import os
import sys
import time

from tqdm import tqdm

from core import NoUrlsFoundError, process_latex


def _print_report(stats: dict, total_time: float) -> None:
    urls_found = stats["urls_found"]
    success_count = stats["success"]
    fail_count = stats["failed"]

    manual_total_time = urls_found * 120.0
    time_saved_sec = manual_total_time - total_time
    time_saved_min = time_saved_sec / 60.0
    speedup_factor = manual_total_time / total_time if total_time > 0 else 0

    print("\n" + "=" * 40)
    print("       PERFORMANCE ANALYSIS REPORT       ")
    print("=" * 40)
    print(f"Total Links Processed:   {urls_found}")
    print(f"Successful Extractions:  {success_count}")
    print(f"Failed Extractions:      {fail_count}")
    print("-" * 40)
    print(f"Automated Runtime:       {total_time:.2f} seconds")
    print(f"Average Time per Link:   {total_time / urls_found:.2f} seconds")
    print("-" * 40)
    print(f"Est. Manual Time (2m/link): {manual_total_time / 60:.1f} minutes")
    print(f"TIME SAVED:              {time_saved_min:.1f} minutes")
    print(f"EFFICIENCY GAIN:         {speedup_factor:.1f}x Faster")
    print("=" * 40)


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

    pbar = None

    def on_url_processed(index: int, total: int, url: str) -> None:
        nonlocal pbar
        if pbar is None:
            print(f"Found {total} URLs. Starting processing...\n")
            pbar = tqdm(total=total, desc="Fetching Citations", unit="link")
        pbar.update(1)

    try:
        result = process_latex(latex_text, on_url_processed=on_url_processed)
    except NoUrlsFoundError as exc:
        print(str(exc))
        sys.exit(0)
    finally:
        if pbar is not None:
            pbar.close()

    with open(bib_path, "w", encoding="utf-8") as bib_file:
        bib_file.write(result["bib"])

    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(result["edited_tex"])

    total_time = time.time() - start_time
    _print_report(result["stats"], total_time)
    print(f"Results saved to: {bib_path}")
