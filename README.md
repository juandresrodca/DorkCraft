# DorkCraft 🔍

> Generate advanced Google search operators from plain English — built for OSINT, academic research, and public information discovery.

**Live site:** https://juandresrodca.github.io/DorkCraft/

---

## What is DorkCraft?

DorkCraft transforms natural language queries into precise [Google dork](https://en.wikipedia.org/wiki/Google_hacking) operators. Instead of remembering syntax like `filetype:pdf intitle:"linux malware"`, you just type:

> *"Find PDF books about Linux malware analysis"*

and DorkCraft builds the query for you.

### Example inputs → outputs

| You type | DorkCraft generates |
|---|---|
| Find PDF books about Linux malware | `filetype:pdf intitle:"linux malware"` |
| LinkedIn profiles for SOC analysts in Ireland | `site:linkedin.com/in intitle:"soc analyst" "Ireland"` |
| Exposed Apache directory listings | `intitle:"index of" "apache" -htm -html` |
| Public GitHub repos about threat intelligence | `site:github.com intitle:"threat intelligence"` |

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | [Astro](https://astro.build) + TypeScript |
| Backend | [FastAPI](https://fastapi.tiangolo.com) (Python 3.9+) |
| Hosting | GitHub Pages (frontend) |
| CI/CD | GitHub Actions |

---

## Project structure

```
DorkCraft/
├── backend/
│   ├── main.py                  # FastAPI app + CORS + routes
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response models
│   ├── services/
│   │   └── dork_generator.py    # Rule-based dork engine
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.astro
│   │   │   ├── Footer.astro
│   │   │   ├── SearchBox.astro
│   │   │   └── ResultCard.astro
│   │   ├── lib/
│   │   │   └── api.ts           # Typed API client
│   │   ├── pages/
│   │   │   └── index.astro      # Main page + all client logic
│   │   └── styles/
│   │       └── global.css       # Design system
│   └── astro.config.mjs
│
├── .github/
│   └── workflows/
│       └── deploy.yml           # Auto-deploy to GitHub Pages
│
└── README.md
```

---

## Running locally

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs available at http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:4321 — the frontend will call the backend at `http://localhost:8000` by default.

---

## Deploying

### Frontend (GitHub Pages)

1. In your repo → **Settings → Pages** → set source to **GitHub Actions**.
2. Push to `main`. The `deploy.yml` workflow builds and deploys automatically.
3. Your site will be live at `https://juandresrodca.github.io/DorkCraft/`.

### Backend (optional)

Deploy the `backend/` folder to any Python host:

| Platform | Notes |
|---|---|
| [Railway](https://railway.app) | One-click Python deploy |
| [Render](https://render.com) | Free tier available |
| [Fly.io](https://fly.io) | Great for small APIs |

After deploying, add the backend URL as a GitHub secret named `VITE_API_URL`. The Actions workflow injects it at build time via `PUBLIC_API_URL`.

---

## Safety & ethics

DorkCraft enforces a blocklist of harmful query patterns at the backend level:

- ❌ Credential or password extraction
- ❌ Credit card / PII data searches
- ❌ Malware delivery
- ❌ Exploit or injection queries
- ❌ Unauthorised access requests

Blocked queries return `{"error": "Unsafe or disallowed query."}` — no dork is generated.

**You are responsible for how you use the results.** Always respect privacy, terms of service, and applicable laws.

---

## Extending DorkCraft (AI-ready)

The `DorkGenerator` class in `backend/services/dork_generator.py` is designed to be a clean extension point:

```python
class DorkGenerator:
    def generate(self, query: str) -> dict:
        # Replace this body with an LLM call (Gemini, Claude, OpenAI)
        # The contract (input/output dict) stays the same
        ...
```

Add new intent categories by extending the `CATEGORIES` dict.
Add new safety rules by extending `BLOCKED_PATTERNS`.

---

## License

MIT — use freely, contribute back.
