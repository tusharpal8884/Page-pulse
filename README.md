### Live Deployment: https://page-pulse-three-flax.vercel.app/




# Page Pulse — Asynchronous Page Audit Engine

[![Live Web App](https://img.shields.io/badge/Live%20App-Page%20Pulse-00C7B7?style=for-the-badge&logo=vercel&logoColor=white)](https://page-pulse-three-flax.vercel.app/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Build Status](https://img.shields.io/github/actions/workflow/status/tusharpal8884/Page-pulse/ci.yml?branch=main&style=for-the-badge&logo=github)](https://github.com/tusharpal8884/Page-pulse/actions)

Page Pulse is an asynchronous web page auditing service built with FastAPI and Python. It analyzes target web pages to extract performance metrics, structural HTML metadata, and OpenGraph parameters. Designed for production standards, it features request tracing via unique IDs, configurable in-memory TTL caching, rate limiting, and an interactive web dashboard.

---

## 🔗 Quick Links

* **Live Deployment:** [https://page-pulse-three-flax.vercel.app/](https://page-pulse-three-flax.vercel.app/)
* **Swagger API Docs:** [https://page-pulse-three-flax.vercel.app/docs](https://page-pulse-three-flax.vercel.app/docs)
* **ReDoc Specification:** [https://page-pulse-three-flax.vercel.app/redoc](https://page-pulse-three-flax.vercel.app/redoc)

---

## ✨ Features

* **Asynchronous Web Scraping:** High-concurrency network fetching built with `httpx` and `BeautifulSoup4`.
* **In-Memory TTL Caching:** Reduces redundant external HTTP requests using `cachetools`.
* **Rate Limiting:** Protects API endpoints against abuse using `slowapi`.
* **Request Tracing:** Custom middleware injects a unique `X-Request-ID` header into every request/response cycle for end-to-end observability.
* **Interactive Web Dashboard:** Modern, responsive UI served directly from the root route (`/`) for instant testing.
* **Automated CI/CD Pipeline:** Built-in GitHub Actions workflow running automated `pytest` suites on every push.

---

## 📑 API Contract

### Base URL

```text
https://page-pulse-three-flax.vercel.app/api/v1
```

### 1. Health Check
Verifies the operational status of the service and API availability.

- Method: `GET`
- Endpoint: `/health`
- Headers: None

Response

- Status Code: `200 OK`
- Content-Type: `application/json`

Example JSON:

```json
{
  "status": "UP"
}
```

### 2. Audit Page URL
Audits a target URL to return metadata, performance response time, and page size metrics.

- Method: `POST`
- Endpoint: `/audit`
- Headers: `Content-Type: application/json`

Request Body (JSON):

```json
{
  "url": "[https://example.com](https://example.com)"
}
```

Successful Response (`200 OK`)

- Headers: `X-Request-ID: <uuid4-string>`
- Content-Type: `application/json`

Example JSON:

```json
{
  "source": "live",
  "data": {
    "url": "[https://example.com](https://example.com)",
    "status": 200,
    "response_time_ms": 142.5,
    "title": "Example Domain",
    "meta_description": "N/A",
    "page_size_bytes": 1256,
    "timestamp": "2026-07-25T17:00:00.000000+00:00"
  }
}
```

Note: If the requested URL was recently audited and resides in the active cache, the `source` field will return `cache` instead of `live`.

Error Responses

**Validation Error (`422 Unprocessable Entity`)**

Occurs when the payload is missing or the provided URL string fails schema validation.

Example JSON:

```json
{
  "detail": [
    {
      "loc": ["body", "url"],
      "msg": "invalid or missing URL scheme",
      "type": "value_error"
    }
  ]
}
```

**Rate Limit Exceeded (`429 Too Many Requests`)**

Occurs when request thresholds exceed defined rate limits (default: 30 requests/minute).

Example JSON:

```json
{
  "error": "Rate limit exceeded: 30 per 1 minute"
}
```

**Target Webpage Fetch Error (`502 Bad Gateway` / `504 Gateway Timeout`)**

Occurs if the target website is unreachable or times out.

Example JSON:

```json
{
  "detail": "Failed to reach target URL: Connection timed out"
}
```

## 🛠️ Tech Stack & Dependencies

- Language: Python 3.11+
- Web Framework: FastAPI
- ASGI Server: Uvicorn
- HTTP Client: HTTPX (Async)
- HTML Parsing: BeautifulSoup4
- Caching: Cachetools
- Rate Limiting: Slowapi
- Testing: Pytest & HTTPX TestClient


## 📁 Project Architecture & Structure

```text
page-pulse/
├── .github/
│   └── workflows/
│       └── ci.yml           
├── app/
│   ├── __init__.py
│   ├── config.py         
│   ├── main.py            
│   ├── middleware.py      
│   ├── schemas.py        
│   └── services/
│       ├── __init__.py
│       ├── audit.py        
│       └── cache.py       
├── tests/
│   ├── __init__.py
│   └── test_audit.py      
├── .env.example
├── requirements.txt
└── README.md
```

## ⚙️ Environment Variables

Create a `.env` file in the project root to override default settings:

| Variable | Type | Default | Description |
|---|---:|---:|---|
| CACHE_TTL_SECONDS | int | 300 | In-memory cache TTL in seconds |
| REQUEST_TIMEOUT_SECONDS | float | 5.0 | HTTP client timeout for outgoing web audits |
| MAX_CONCURRENT_REQUESTS | int | 5 | Concurrency cap for outgoing scraping tasks |
| RATE_LIMIT_STRING | str | 30/minute | Rate limit setting applied to API endpoints |

## 💻 Local Development Setup

Clone the repository:

```bash
git clone https://github.com/tusharpal8884/Page-pulse.git
cd Page-pulse
```

Create and activate a virtual environment:

```bash
# On Windows PowerShell:
python -m venv .venv
\.venv\Scripts\Activate.ps1

# On macOS/Linux:
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the local development server:

```bash
uvicorn app.main:app --reload
```

Access the application:

- Dashboard UI: http://127.0.0.1:8000/
- Swagger Docs: http://127.0.0.1:8000/docs

Run tests:

```bash
pytest
```

## 📜 Notice

Built for Digital Heroes Training Task.

---


