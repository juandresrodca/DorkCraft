"""
DorkCraft FastAPI Backend
=========================
Entry point for the DorkCraft API. Exposes:
  POST /generate   — generate a Google dork from a natural language query
  GET  /health     — liveness check

Run locally:
    uvicorn main:app --reload --port 8000

CORS is configured to allow the Astro dev server (localhost:4321) and
the GitHub Pages frontend. Update ALLOWED_ORIGINS if you deploy elsewhere.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models.schemas import GenerateRequest, DorkResponse, ErrorResponse
from services.dork_generator import DorkGenerator

# ---------------------------------------------------------------------------
# App initialisation
# ---------------------------------------------------------------------------

app = FastAPI(
    title="DorkCraft API",
    description="Generate safe and effective Google dork queries from plain English.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — allow the frontend origins
# Update ALLOWED_ORIGINS to match your GitHub Pages URL before deploying.
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS = [
    "http://localhost:4321",       # Astro dev server
    "http://127.0.0.1:4321",
    "https://*.github.io",         # GitHub Pages (wildcard — browsers check origin exactly,
                                   # so add your specific Pages URL below too)
    # "https://yourusername.github.io",  # <- uncomment and fill in
    "*",                           # Open for demo; restrict in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# Singleton generator (stateless, safe to share across requests)
generator = DorkGenerator()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["meta"])
async def health_check():
    """Liveness endpoint — confirms the API is running."""
    return {"status": "ok", "service": "dorkcraft-api"}


@app.post(
    "/generate",
    response_model=DorkResponse,
    responses={400: {"model": ErrorResponse}},
    tags=["dorks"],
    summary="Generate a Google dork from a plain English query",
)
async def generate_dork(request: GenerateRequest):
    """
    Accept a natural language query and return a structured Google dork.

    Example request body:
    ```json
    { "query": "Find PDF books about Linux malware analysis" }
    ```

    Example success response:
    ```json
    {
      "dork": "filetype:pdf intitle:\\"linux malware analysis\\"",
      "explanation": ["filetype:pdf restricts to PDF files", ...],
      "variations": ["filetype:pdf \\"linux malware\\"", ...],
      "category": "documents"
    }
    ```
    """
    result = generator.generate(request.query)

    # The generator returns {"error": "..."} for refused queries
    if "error" in result:
        return JSONResponse(
            status_code=400,
            content={"error": result["error"]}
        )

    return result


# ---------------------------------------------------------------------------
# Development entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
