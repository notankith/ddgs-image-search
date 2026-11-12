import os
import time
from functools import wraps

from ddgs import DDGS
from flask import Flask, jsonify, request

app = Flask(__name__)
API_KEY = os.getenv("API_KEY", "").strip()


def require_api_key(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if API_KEY:
            supplied = request.headers.get("X-API-Key") or request.args.get("key")
            if supplied != API_KEY:
                return jsonify(ok=False, error="Unauthorized"), 401
        return fn(*args, **kwargs)
    return wrapped


@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def value(data, *keys, default=None):
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return default


@app.get("/")
def index():
    return jsonify(
        name="DDGS Image Search API",
        ok=True,
        endpoints={
            "health": "/health",
            "search": "/api/search?q=cat&n=20",
            "docs": "https://github.com/notankith/ddgs-image-search"
        }
    )


@app.get("/health")
@app.get("/api/health")
def health():
    return jsonify(ok=True, service="ddgs-image-search", auth_required=bool(API_KEY))


@app.route("/api/search", methods=["GET", "POST", "OPTIONS"])
@require_api_key
def search_images():
    if request.method == "OPTIONS":
        return "", 204

    body = request.get_json(silent=True) or {}
    params = request.args

    def get_param(*keys, default=None):
        return value(body, *keys, default=value(params, *keys, default=default))

    query = str(get_param("q", "query", default="") or "").strip()
    if not query:
        return jsonify(ok=False, error="Missing search query. Pass q or query."), 400

    try:
        max_results = max(1, min(int(get_param("n", "max_results", default=20)), 100))
        page = max(1, int(get_param("page", default=1)))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="n/max_results and page must be integers."), 400

    options = {
        "region": get_param("region", default="us-en"),
        "safesearch": get_param("safe", "safesearch", default="moderate"),
        "timelimit": get_param("time", default=None) or None,
        "size": get_param("size", default=None) or None,
        "color": get_param("color", default=None) or None,
        "type_image": get_param("type", "type_image", default=None) or None,
        "layout": get_param("layout", default=None) or None,
        "license_image": get_param("license", "license_image", default=None) or None,
        "page": page,
        "max_results": max_results,
    }
    backend = get_param("backend", default=None)
    if backend:
        options["backend"] = backend

    started = time.perf_counter()
    try:
        proxy = get_param("proxy", default=None) or os.getenv("DDGS_PROXY") or None
        with DDGS(proxy=proxy) as ddgs:
            results = ddgs.images(query, **options)
        return jsonify(
            ok=True,
            query=query,
            count=len(results),
            ms=round((time.perf_counter() - started) * 1000),
            results=results,
        )
    except Exception as exc:
        message = str(exc)
        status = 429 if "ratelimit" in type(exc).__name__.lower() or "202" in message else 502
        app.logger.exception("Image search failed")
        return jsonify(
            ok=False,
            error=f"{type(exc).__name__}: {message}",
        ), status


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "1252")), threaded=True)
