from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse, HTMLResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import httpx

from app.config import settings
from app.schemas import AuditRequest, AuditResponse
from app.services.cache import cache_service
from app.services.audit import perform_audit
from app.middleware import RequestIDMiddleware

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Page Pulse API", version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(RequestIDMiddleware)

# Full Interactive Frontend Web Page
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Page Pulse - Production URL Auditor</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    </head>
    <body class="bg-slate-900 text-slate-100 min-h-screen flex flex-col justify-between font-sans">
        
        <!-- Header -->
        <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
            <div class="max-w-5xl mx-auto px-6 py-4 flex justify-between items-center">
                <div class="flex items-center gap-3">
                    <div class="bg-indigo-600 text-white p-2 rounded-lg">
                        <i class="fa-solid fa-chart-line text-xl"></i>
                    </div>
                    <span class="font-bold text-xl tracking-tight text-white">PagePulse</span>
                </div>
                <a href="/docs" target="_blank" class="text-sm font-medium text-slate-400 hover:text-indigo-400 transition">
                    API Docs <i class="fa-solid fa-arrow-up-right-from-square text-xs ml-1"></i>
                </a>
            </div>
        </header>

        <!-- Main Body -->
        <main class="max-w-4xl mx-auto px-6 py-12 w-full flex-1">
            <div class="text-center mb-10">
                <h1 class="text-4xl font-extrabold text-white sm:text-5xl tracking-tight">URL Performance Audit</h1>
                <p class="mt-3 text-lg text-slate-400">Run production-grade audits with automated rate-limiting, concurrency control, and caching.</p>
            </div>

            <!-- Input Form -->
            <div class="bg-slate-800/80 border border-slate-700 rounded-xl p-6 shadow-xl mb-8">
                <form id="auditForm" onsubmit="handleAudit(event)" class="space-y-4">
                    <label class="block text-sm font-medium text-slate-300">Target Webpage URL</label>
                    <div class="flex flex-col sm:flex-row gap-3">
                        <input type="url" id="urlInput" required placeholder="https://example.com"
                            class="flex-1 px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-100 placeholder-slate-500">
                        <button type="submit" id="submitBtn"
                            class="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 font-semibold rounded-lg transition flex items-center justify-center gap-2 text-white">
                            <i class="fa-solid fa-bolt"></i> Run Audit
                        </button>
                    </div>
                </form>

                <!-- Quick Presets -->
                <div class="mt-4 flex flex-wrap items-center gap-2 text-xs text-slate-400">
                    <span>Try testing:</span>
                    <button onclick="setAndAudit('https://example.com')" class="px-2.5 py-1 bg-slate-700/50 hover:bg-slate-700 rounded text-slate-300 transition">https://example.com</button>
                    <button onclick="setAndAudit('https://github.com')" class="px-2.5 py-1 bg-slate-700/50 hover:bg-slate-700 rounded text-slate-300 transition">https://github.com</button>
                    <button onclick="setAndAudit('https://wikipedia.org')" class="px-2.5 py-1 bg-slate-700/50 hover:bg-slate-700 rounded text-slate-300 transition">https://wikipedia.org</button>
                </div>
            </div>

            <!-- Loading Spinner -->
            <div id="loadingState" class="hidden text-center py-12">
                <div class="inline-block animate-spin rounded-full h-10 w-10 border-4 border-indigo-500 border-t-transparent"></div>
                <p class="mt-4 text-slate-400 font-medium">Fetching webpage metrics...</p>
            </div>

            <!-- Error Banner -->
            <div id="errorState" class="hidden bg-rose-950/50 border border-rose-800 text-rose-300 p-4 rounded-xl mb-8">
                <div class="flex items-center gap-3">
                    <i class="fa-solid fa-triangle-exclamation text-xl"></i>
                    <div>
                        <h4 class="font-bold" id="errorTitle">Audit Failed</h4>
                        <p class="text-sm" id="errorMessage"></p>
                    </div>
                </div>
            </div>

            <!-- Results Card -->
            <div id="resultsCard" class="hidden bg-slate-800/80 border border-slate-700 rounded-xl p-6 shadow-xl space-y-6">
                <div class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-700 pb-4">
                    <div>
                        <span class="text-xs uppercase tracking-wider font-semibold text-slate-400">Target URL</span>
                        <h3 class="text-lg font-semibold text-white break-all" id="resUrl"></h3>
                    </div>
                    <div id="sourceBadge"></div>
                </div>

                <!-- Metrics Grid -->
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div class="bg-slate-900/60 p-4 rounded-lg border border-slate-800">
                        <span class="text-xs text-slate-400">HTTP Status</span>
                        <div class="text-2xl font-bold text-emerald-400 mt-1" id="resStatus">--</div>
                    </div>
                    <div class="bg-slate-900/60 p-4 rounded-lg border border-slate-800">
                        <span class="text-xs text-slate-400">Response Time</span>
                        <div class="text-2xl font-bold text-indigo-400 mt-1" id="resTime">--</div>
                    </div>
                    <div class="bg-slate-900/60 p-4 rounded-lg border border-slate-800">
                        <span class="text-xs text-slate-400">Page Size</span>
                        <div class="text-2xl font-bold text-sky-400 mt-1" id="resSize">--</div>
                    </div>
                    <div class="bg-slate-900/60 p-4 rounded-lg border border-slate-800">
                        <span class="text-xs text-slate-400">Timestamp</span>
                        <div class="text-xs font-semibold text-slate-300 mt-2 truncate" id="resTimeISO">--</div>
                    </div>
                </div>

                <!-- Page Meta Details -->
                <div class="space-y-4 pt-2">
                    <div>
                        <span class="text-xs uppercase tracking-wider font-semibold text-slate-400">Page Title</span>
                        <p class="text-slate-200 font-medium mt-1 bg-slate-900/40 p-3 rounded border border-slate-800" id="resTitle"></p>
                    </div>
                    <div>
                        <span class="text-xs uppercase tracking-wider font-semibold text-slate-400">Meta Description</span>
                        <p class="text-slate-300 text-sm mt-1 bg-slate-900/40 p-3 rounded border border-slate-800" id="resDesc"></p>
                    </div>
                </div>
            </div>
        </main>

        <!-- Mandatory Verification Footer -->
        <footer class="border-t border-slate-800 py-6 text-center text-sm text-slate-500">
            <p>Built for Digital Heroes Training Task - <a href="https://digitalheroesco.com" target="_blank" rel="noopener noreferrer" class="text-indigo-400 hover:underline">digitalheroesco.com</a></p>
        </footer>

        <!-- Automated Frontend Interactivity Script -->
        <script>
            async function handleAudit(event) {
                if (event) event.preventDefault();
                const url = document.getElementById('urlInput').value;
                if (!url) return;

                showLoading(true);
                hideError();
                hideResults();

                try {
                    const response = await fetch('/api/v1/audit', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url })
                    });

                    const data = await response.json();

                    if (!response.ok) {
                        const errMsg = data.error?.message || data.error?.details?.[0] || 'An unexpected error occurred.';
                        showError(data.error?.code || 'ERROR', errMsg);
                    } else {
                        renderResults(data);
                    }
                } catch (err) {
                    showError('NETWORK_ERROR', 'Failed to communicate with the server.');
                } finally {
                    showLoading(false);
                }
            }

            function setAndAudit(url) {
                document.getElementById('urlInput').value = url;
                handleAudit(null);
            }

            function renderResults(res) {
                const item = res.data;
                document.getElementById('resUrl').innerText = item.url;
                document.getElementById('resStatus').innerText = item.status;
                document.getElementById('resTime').innerText = item.response_time_ms + ' ms';
                document.getElementById('resSize').innerText = (item.page_size_bytes / 1024).toFixed(1) + ' KB';
                document.getElementById('resTimeISO').innerText = new Date(item.timestamp).toLocaleTimeString();
                document.getElementById('resTitle').innerText = item.title;
                document.getElementById('resDesc').innerText = item.meta_description;

                // Cache vs Live badge UI styling
                const badgeContainer = document.getElementById('sourceBadge');
                if (res.source === 'cache') {
                    badgeContainer.innerHTML = `<span class="px-3 py-1 bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded-full text-xs font-semibold"><i class="fa-solid fa-bolt"></i> Served from Cache</span>`;
                } else {
                    badgeContainer.innerHTML = `<span class="px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-full text-xs font-semibold"><i class="fa-solid fa-arrows-rotate"></i> Live Audit</span>`;
                }

                document.getElementById('resultsCard').classList.remove('hidden');
            }

            function showLoading(state) {
                document.getElementById('loadingState').classList.toggle('hidden', !state);
                document.getElementById('submitBtn').disabled = state;
            }

            function showError(title, msg) {
                document.getElementById('errorTitle').innerText = title;
                document.getElementById('errorMessage').innerText = msg;
                document.getElementById('errorState').classList.remove('hidden');
            }

            function hideError() { document.getElementById('errorState').classList.add('hidden'); }
            function hideResults() { document.getElementById('resultsCard').classList.add('hidden'); }
        </script>
    </body>
    </html>
    """

@app.get("/api/v1/health")
async def health_check():
    return {"status": "UP"}

@app.post("/api/v1/audit", response_model=AuditResponse)
@limiter.limit(settings.RATE_LIMIT_STRING)
async def audit_url(request: Request, body: AuditRequest):
    target_url = str(body.url)
    
    # 1. Check Cache
    cached_result = cache_service.get(target_url)
    if cached_result:
        return {"source": "cache", "data": cached_result}

    # 2. Perform Audit with Resilience
    try:
        result = await perform_audit(target_url)
        cache_service.set(target_url, result)
        return {"source": "live", "data": result}
        
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"code": "TIMEOUT", "message": "The upstream target URL timed out."}
        )
    except httpx.HTTPError as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "BAD_GATEWAY", "message": f"Failed to reach upstream target: {str(err)}"}
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}
        )

# Custom Error Response Formatter
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail if isinstance(exc.detail, dict) else {"code": "ERROR", "message": exc.detail}}
    )