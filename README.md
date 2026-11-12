# DDGS Image Search API

A small Flask API that returns DuckDuckGo image-search results as JSON using the `ddgs` Python package.

## Deploy

Configured for Render with:
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app`
- Health check: `/health`

## Endpoints

### Health
`GET /health` (also available at `GET /api/health`)

### Search
`GET /api/search?q=cat&n=20`

Useful parameters:
- `q` or `query`: search query (required)
- `n` or `max_results`: number of results, 1-100 (default 20)
- `page`: page number (default 1)
- `safe`: `on`, `moderate`, or `off`
- `region`: region code (default `us-en`)
- `size`: `Small`, `Medium`, `Large`, or `Wallpaper`
- `layout`: `Square`, `Tall`, or `Wide`
- `color`, `type`, `time`, `license`, `backend`

POST is also supported with a JSON body:
```json
{ "q": "red sports car", "n": 30, "safe": "moderate" }
```

Successful responses contain `ok`, `query`, `count`, `ms`, and `results`. Each result includes the image metadata returned by DDGS, including image/thumbnail URLs where available.

## Optional API key

Set the Render environment variable `API_KEY` to require authentication. Send it as:
- Header: `X-API-Key: your-key`
- Or query parameter: `?key=your-key`

No key is required when `API_KEY` is unset.

## Local run

```bash
pip install -r requirements.txt
python app.py
```
