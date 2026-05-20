import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from main import NoUrlsFoundError, process_latex

STATIC_DIR = Path(__file__).parent / "static"
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))

app = FastAPI(title="AutoBib", version="1.0.0")

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def index():
    index_path = STATIC_DIR / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="UI not found")
    return FileResponse(index_path)


@app.post("/api/process")
async def process_tex_file(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".tex"):
        raise HTTPException(status_code=400, detail="Please upload a .tex file.")

    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    try:
        latex_text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded.") from exc

    try:
        result = process_latex(latex_text)
    except NoUrlsFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Processing failed: {exc}") from exc

    stats = result["stats"]
    if stats["urls_found"] > 0 and stats["success"] == 0:
        raise HTTPException(
            status_code=502,
            detail=(
                "Could not generate any citations. "
                "Check your network connection and set SERPER_API_KEY in the environment."
            ),
        )

    return {
        "edited_tex": result["edited_tex"],
        "bib": result["bib"],
        "stats": stats,
        "original_filename": file.filename,
    }
