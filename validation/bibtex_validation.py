# validation/bibtex_validation.py
import logging
import bibtexparser
from bibtexparser.customization import homogenize_latex_encoding

def validate_bibtex(bib: str) -> bool:
    try:
        # Load BibTeX normally
        bib_db = bibtexparser.loads(bib)
        # Optional: apply homogenization manually
        bib_db.entries = [homogenize_latex_encoding(entry) for entry in bib_db.entries]
        return True
    except Exception as e:
        logging.error(f"BibTeX validation failed: {e}")
        return False
