import logging
import requests
import xmltodict

def extract_pdf_metadata(pdf_url: str):
    try:
        pdf_bytes = requests.get(pdf_url, timeout=12).content
        files = {"input": ("paper.pdf", pdf_bytes, "application/pdf")}
        r = requests.post("http://localhost:8070/api/processHeaderDocument", files=files, timeout=30)

        if r.status_code == 200:
            data = xmltodict.parse(r.text)["TEI"]["teiHeader"]["fileDesc"]["sourceDesc"]["biblStruct"]["analytic"]
            return {
                "title": data["title"]["#text"],
                "author": [a["persName"]["#text"] for a in data["author"]],
                "year": data["date"]["@when"][:4],
                "URL": pdf_url,
            }

    except Exception as e:
        logging.warning(f"PDF extraction failed: {e}")

    return None
