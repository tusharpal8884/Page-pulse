import asyncio
import time
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup
from app.config import settings

# Global concurrency semaphore
semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)

async def perform_audit(target_url: str) -> dict:
    async with semaphore:
        start_time = time.perf_counter()
        
        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS, follow_redirects=True) as client:
            headers = {"User-Agent": "PagePulse-AuditBot/1.0"}
            response = await client.get(target_url, headers=headers)
        
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        
        soup = BeautifulSoup(response.text, "html.parser")
        title_tag = soup.find("title")
        meta_desc = soup.find("meta", attrs={"name": "description"})
        
        return {
            "url": target_url,
            "status": response.status_code,
            "response_time_ms": elapsed_ms,
            "title": title_tag.string.strip() if title_tag and title_tag.string else "N/A",
            "meta_description": meta_desc.get("content", "N/A") if meta_desc else "N/A",
            "page_size_bytes": len(response.content),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }