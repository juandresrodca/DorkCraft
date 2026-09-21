# Self-hosting DorkCraft

The hosted demo at <https://juandresrodca.github.io/DorkCraft/> is fine for trying
the tool. It is not fine for a SOC, because every query you type goes to somebody
else's API. This page is how you run both halves yourself.

Two things are worth knowing before you start:

- **The backend needs no secrets, no database and no outbound network access.**
  `DorkGenerator` is a rule engine over the text you send it. It does not call
  Google, it does not call an LLM, it does not phone home. That is what makes a
  fully offline deployment possible at all — see [Running fully offline](#running-fully-offline).
- **The shipped `ALLOWED_ORIGINS` ends with `"*"`.** That is a demo default and
  [`SECURITY.md`](../SECURITY.md) says so. Changing it is step one of every
  deployment below, not an optional hardening pass.

---

## Contents

| Section | Use it when |
|---|---|
| [Docker](#docker) | You want one container you can run anywhere. |
| [Docker Compose](#docker-compose-both-halves) | You want the API and the static frontend together. |
| [Render](#render) | You want a free managed host and `render.yaml` is already here. |
| [Environment variables](#environment-variables) | You are wiring the two halves together. |
| [Reverse proxy](#reverse-proxy) | You are putting it on a real hostname with TLS. |
| [Running fully offline](#running-fully-offline) | Air-gapped network, or no egress allowed. |

---

## Docker

There is no `Dockerfile` in the repository, deliberately — the backend is four
dependencies and a directory, and pinning a base image in the repo dates faster
than the code does. Write this one next to `backend/`:

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Dependencies first, so a code change does not invalidate the layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as a non-root user. Nothing here needs to write to the filesystem.
RUN useradd --create-home --shell /usr/sbin/nologin dorkcraft
USER dorkcraft

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run it:

```bash
cd backend
docker build -t dorkcraft-api .
docker run --rm -p 8000:8000 dorkcraft-api
curl -s localhost:8000/health        # {"status":"ok","service":"dorkcraft-api"}
```

`requirements.txt` pins exact versions, so the image is reproducible as long as
the base tag is. Pin the base by digest (`python:3.12-slim@sha256:…`) if you need
it to be reproducible full stop.

> **Note on the port.** `main.py` hardcodes 8000 in its `__main__` block, which
> only runs under `python main.py`. The `CMD` above passes the port to `uvicorn`
> directly, so map it with `-p` or override the command — do not edit the module.

## Docker Compose (both halves)

The frontend is a static Astro build, so it does not need a Node process in
production — only a web server that serves `frontend/dist/`.

```yaml
# docker-compose.yml
services:
  api:
    build: ./backend
    restart: unless-stopped
    expose: ["8000"]

  web:
    image: nginx:1.27-alpine
    restart: unless-stopped
    ports: ["8080:80"]
    volumes:
      - ./frontend/dist:/usr/share/nginx/html:ro
    depends_on: [api]
```

Build the frontend first, and tell it where the API lives at **build** time —
Astro inlines `PUBLIC_API_URL` into the bundle, so changing it later means
rebuilding:

```bash
cd frontend
PUBLIC_API_URL=http://localhost:8080/api npm run build
cd .. && docker compose up -d
```

Two details that bite people here:

- `astro.config.mjs` sets `base: '/DorkCraft'`, because the demo is served from a
  GitHub Pages project path. Serving from the root of your own host means setting
  `base: '/'` before you build, or your assets 404.
- `trailingSlash: 'always'` is set for the same reason. Keep it, and make sure the
  proxy in front does not strip trailing slashes.

## Render

[`render.yaml`](../render.yaml) already describes the API service, so the
walkthrough is short:

1. **New → Blueprint** in the Render dashboard, point it at your fork.
2. Render reads `render.yaml`, finds `rootDir: backend`, and builds with
   `pip install -r requirements.txt`.
3. The start command is `uvicorn main:app --host 0.0.0.0 --port $PORT`. Render
   injects `$PORT`; do not hardcode it.
4. Note the service URL it gives you — that is your `PUBLIC_API_URL`.

Two amendments worth making to the blueprint for a real deployment:

- `PYTHON_VERSION` is `3.9.0`, which is the floor the README claims. Raise it to
  `3.12` unless you specifically need 3.9 — the pinned dependencies all support it.
- Add a health check path so Render restarts a wedged instance:

  ```yaml
      healthCheckPath: /health
  ```

On the free tier the service spins down when idle, and the first request after
that takes several seconds. That is a Render behaviour, not a DorkCraft bug.

## Environment variables

There are exactly two knobs, and only one of them is an environment variable.

| Name | Half | Set at | Default | What it does |
|---|---|---|---|---|
| `PUBLIC_API_URL` | Frontend | **Build** time | `http://localhost:8000` | Base URL the browser calls. Read in [`frontend/src/lib/api.ts`](../frontend/src/lib/api.ts). |
| `PORT` | Backend | Run time | — | Supplied by the platform (Render, Fly, Railway) and passed to `uvicorn`. |
| `ALLOWED_ORIGINS` | Backend | **Source** | see below | Not an environment variable yet — it is a list in [`backend/main.py`](../backend/main.py). |

`ALLOWED_ORIGINS` being a source constant rather than configuration is a rough
edge. Until it moves, edit it before you deploy:

```python
ALLOWED_ORIGINS = [
    "https://dorkcraft.example.com",   # your frontend origin, exactly
]
```

Drop the `"*"` entry and the `"https://*.github.io"` wildcard. Browsers match the
`Origin` header exactly, so the wildcard never did what it looks like it does —
the `"*"` below it was doing all the work.

`allow_credentials=False` is already set, so a permissive origin list is not a
session-theft risk here. What it costs you is quota: with `"*"` in place, anyone's
page can call your instance.

## Reverse proxy

Putting the API on the same origin as the frontend removes CORS from the picture
entirely, which is the simplest thing you can do for yourself:

```nginx
server {
    listen 443 ssl http2;
    server_name dorkcraft.example.com;

    # TLS directives omitted — use whatever your certificate tooling emits.

    location / {
        root /srv/dorkcraft;          # frontend/dist
        try_files $uri $uri/ =404;
    }

    location /api/ {
        proxy_pass         http://127.0.0.1:8000/;
        proxy_set_header   Host $host;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;

        # The rule engine is CPU-bound and fast. A slow request is a stuck one.
        proxy_read_timeout 15s;

        limit_req zone=dorkcraft burst=20 nodelay;
    }
}
```

With that in place, build the frontend with `PUBLIC_API_URL=/api` and the
`ALLOWED_ORIGINS` question disappears — the browser never makes a cross-origin
request.

**Rate limiting is your job.** [`SECURITY.md`](../SECURITY.md) is explicit that the
API ships without any, and the proxy is the right place for it:

```nginx
# http { } block
limit_req_zone $binary_remote_addr zone=dorkcraft:10m rate=10r/s;
```

`/health` is unauthenticated and returns no detail beyond liveness, so it is safe
to leave exposed for your monitoring. `/docs` and `/redoc` are also open — block
them at the proxy if you would rather not publish the schema:

```nginx
    location ~ ^/api/(docs|redoc|openapi.json)$ { return 404; }
```

## Running fully offline

DorkCraft's backend makes no outbound connections. That is unusual enough for an
OSINT tool to be worth stating plainly: you can run the API on a network with no
egress at all and it behaves identically.

What that gets you, and what it does not:

- **The generated dork never leaves your machine.** Neither does the query you
  typed. For work where the *question* is sensitive — and in threat intel it often
  is — this is the whole point of self-hosting.
- **Running the dork still needs Google.** DorkCraft builds the operator string;
  it does not execute a search. The frontend gives you the query to copy.
- **Only the build needs the internet.** `pip install` and `npm ci` pull from PyPI
  and npm. Build the image and the static bundle on a connected machine, move the
  artefacts across, and nothing on the isolated side needs a registry.

```bash
# On a connected machine
docker build -t dorkcraft-api ./backend
docker save dorkcraft-api | gzip > dorkcraft-api.tar.gz
(cd frontend && PUBLIC_API_URL=/api npm ci && npm run build)
tar czf dorkcraft-web.tar.gz -C frontend dist

# On the isolated host
gunzip -c dorkcraft-api.tar.gz | docker load
```

Verify the claim rather than trusting this page — run the container with no
network and confirm it still answers:

```bash
docker run --rm --network none dorkcraft-api \
  python -c "from services.dork_generator import DorkGenerator; \
             print(DorkGenerator().generate('Find PDF books about Linux malware'))"
```

---

## Checklist before you expose it

- [ ] `ALLOWED_ORIGINS` contains your origins and nothing else.
- [ ] Rate limiting is configured at the proxy or the platform edge.
- [ ] `/docs` and `/redoc` are blocked, or you are content to publish the schema.
- [ ] The frontend was built with the `PUBLIC_API_URL` you actually deploy to.
- [ ] `base` in `astro.config.mjs` matches the path you serve from.
- [ ] TLS terminates somewhere, and `X-Forwarded-Proto` reaches the app.
- [ ] You have read the responsible-use section of [`SECURITY.md`](../SECURITY.md)
      and accept that the blocklist is a keyword filter, not a guarantee.
