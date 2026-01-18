# validation/bibtex_validation.py
import logging
import bibtexparser
from bibtexparser.customization import homogenize_latex_encoding

def validate_bibtex(bib: str) -> bool:
    try:
        # Configure parser to allow non-standard entry types
        parser = bibtexparser.bparser.BibTexParser(common_strings=True)
        parser.ignore_nonstandard_types = False
        
        # Load BibTeX normally
        bib_db = bibtexparser.loads(bib, parser=parser)
        # Optional: apply homogenization manually
        bib_db.entries = [homogenize_latex_encoding(entry) for entry in bib_db.entries]
        return True
    except Exception as e:
        logging.error(f"BibTeX validation failed: {e}")
        return False
