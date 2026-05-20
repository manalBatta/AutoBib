# Deploying AutoBib

AutoBib runs as a single FastAPI app: the web UI at `/` and the processing API at `POST /api/process`.

## Local development

```bash
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```

Open http://localhost:8000

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Recommended for production | OpenAI API key for BibTeX formatting and fixes |
| `USE_MOCK` | No | Set to `true` to skip OpenAI calls (testing). Defaults to mock mode when `OPENAI_API_KEY` is unset |
| `MAX_UPLOAD_BYTES` | No | Max `.tex` upload size in bytes (default: 5242880 = 5 MB) |
| `PORT` | Set by host | HTTP port (Render/Railway inject this automatically) |

## Render

1. Push this repo to GitHub.
2. In Render: **New → Web Service** → connect the repo.
3. Use [render.yaml](render.yaml) or set manually:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn api:app --host 0.0.0.0 --port $PORT`
   - **Health check path:** `/health`
4. Add `OPENAI_API_KEY` under **Environment**.
5. Set `USE_MOCK=false` for real citation processing.
6. Increase request timeout if you process large files (Settings → request timeout, e.g. 600s).

## Railway

1. Push this repo to GitHub.
2. **New Project → Deploy from GitHub** → select this repo.
3. Railway reads [Procfile](Procfile) for the start command.
4. Add `OPENAI_API_KEY` in **Variables**.
5. Set `USE_MOCK=false` for production.

## CLI (unchanged)

```bash
python main.py path/to/file.tex
```

## Troubleshooting empty output

- **Terminal shows `No arxiv metadata found` / `No metadata found`:** arXiv may be rate-limiting requests (HTTP 429). Wait a few minutes and retry, or process fewer URLs at once.
- **OpenAI quota errors:** Set `USE_MOCK=true` in `.env` to use the built-in BibTeX template (no OpenAI calls). AutoBib will also fall back to this template if OpenAI fails.
- **First request returned 400:** Usually means the file had no URLs or the upload failed; pick a `.tex` file and try again.
- **Downloads look empty but UI says success:** Restart uvicorn after changing `.env`, then re-process the file.
