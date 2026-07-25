# Live Link -https://page-pulse-three-flax.vercel.app/


# Page Pulse
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=flat&logo=fastapi&logoColor=white)
![Build Status](https://github.com/tusharpal8884/Page-pulse-api/actions/workflows/ci.yml/badge.svg)


Page Pulse is a FastAPI-based URL auditing service that fetches a webpage, extracts basic metadata, and returns a structured audit result. It includes request ID tracing, in-memory caching, rate limiting, and a simple web UI for testing the API.

## Features

- FastAPI-based REST API
- URL audit endpoint with live and cached responses
- Basic HTML metadata extraction for page title and meta description
- Request ID middleware for tracing
- In-memory TTL caching
- Rate limiting
- Simple interactive frontend served from the root route

## Project Structure

```text
page-pulse/
├── app/
│   ├── config.py
│   ├── main.py
│   ├── middleware.py
│   ├── schemas.py
│   └── services/
│       ├── audit.py
│       └── cache.py
├── tests/
│   └── test_audit.py
├── requirements.txt
└── README.md
```

## Tech Stack

- Python 3.11+
- FastAPI
- Uvicorn
- httpx
- BeautifulSoup4
- cachetools
- slowapi
- pytest

## Installation

1. Clone the repository:

```bash
git clone <https://github.com/tusharpal8884/Page-pulse.git>
cd page-pulse
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root if you want to override defaults.

Example:

```env
CACHE_TTL_SECONDS=300
REQUEST_TIMEOUT_SECONDS=5.0
MAX_CONCURRENT_REQUESTS=5
RATE_LIMIT_STRING=30/minute
```

## Running the Application

Start the server with:

```bash
uvicorn app.main:app --reload
```

Then open:

- Home UI: http://127.0.0.1:8000/
- API docs: http://127.0.0.1:8000/docs

## API Endpoints

### Health Check

- Method: GET
- Path: `/api/v1/health`

Response:

```json
{
  "status": "UP"
}
```

### Audit URL

- Method: POST
- Path: `/api/v1/audit`
- Content-Type: `application/json`

Request body:

```json
{
  "url": "https://example.com"
}
```

Successful response:

```json
{
  "source": "live",
  "data": {
    "url": "https://example.com",
    "status": 200,
    "response_time_ms": 142.5,
    "title": "Example Domain",
    "meta_description": "N/A",
    "page_size_bytes": 1256,
    "timestamp": "2026-07-25T17:00:00.000000+00:00"
  }
}
```

## Testing

Run tests with:

```bash
pytest
```

## Notes

- The service uses an in-memory cache, so cached values are reset when the server restarts.
- The audit endpoint validates that the provided URL is a valid HTTP/HTTPS URL.
