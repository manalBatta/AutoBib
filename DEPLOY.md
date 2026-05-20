# Deploying AutoBib

AutoBib runs as a single FastAPI app: the web UI at `/` and the processing API at `POST /api/process`.

## Local development

```bash
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```

Open http://localhost:8000

Set `SERPER_API_KEY` in `config/.env` (see `config/settings.py`) for citation enrichment.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SERPER_API_KEY` | Yes (production) | Serper API key for metadata enrichment during BibTeX formatting |
| `MAX_UPLOAD_BYTES` | No | Max `.tex` upload size in bytes (default: 5242880 = 5 MB) |
| `PORT` | Set by host | HTTP port (Render injects this automatically) |

## Render

1. Push this folder to GitHub (use it as the repo root, or set **Root Directory** to `AutoBib-main/AutoBib-main` if the repo is larger).
2. In Render: **New → Web Service** → connect the repo.
3. Use [render.yaml](render.yaml) or set manually:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn api:app --host 0.0.0.0 --port $PORT`
   - **Health check path:** `/health`
4. Add `SERPER_API_KEY` under **Environment**.
5. Increase **request timeout** for large `.tex` files (Settings → request timeout, e.g. 300–600s). Each URL may call several external APIs.

## Railway

1. Push this repo to GitHub.
2. **New Project → Deploy from GitHub** → select this repo.
3. Railway reads [Procfile](Procfile) for the start command.
4. Add `SERPER_API_KEY` in **Variables**.

## CLI (unchanged)

```bash
python main.py path/to/file.tex
```

## Troubleshooting

- **No citations extracted:** Verify `SERPER_API_KEY` is set on the server and reachable. Check logs for arXiv/Crossref rate limits (HTTP 429).
- **Request timeout on Render:** Reduce URLs per file or increase the service request timeout.
- **First request returned 400:** Usually means the file had no URLs or the upload failed.
- **Presentation slides:** Open [presentation.html](presentation.html) in a browser (not served by the app).
