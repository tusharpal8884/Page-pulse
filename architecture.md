
##                     PAGE PULSE: SYSTEM ARCHITECTURE & DESIGN
##           Scaling Strategy for 10,000 Audits/Day & 500 Peak Concurrency


# 1. SYSTEM ARCHITECTURE & DATA FLOW

[Components Overview]
- API Layer: Stateless FastAPI application instances behind an Application 
  Load Balancer (ALB). Autoscales based on CPU/Memory usage and queue lag.
- Edge / CDN: Cloudflare Edge Network for DDoS protection, TLS termination, 
  and public API response caching.
- Queueing & Asynchronous Workers: Celery distributed task queue backed by 
  a Redis broker to isolate user API requests from heavy web scraping tasks.
- In-Memory Caching & State: Redis Cluster for:
    * Fast TTL-based audit result caching.
    * Distributed rate-limiting tracking.
    * Real-time job state handling (PENDING, PROCESSING, SUCCESS, FAILED).
- Data Persistence: PostgreSQL (AWS RDS) storing user profiles, historical 
  audits, and audit logs.
- Blob Storage: AWS S3 for long-term raw HTML snapshots and asset storage.


## [System Topology & ASCII Architecture Diagram]
```text 
+-------------------+       +-----------------------+
|  Client / Web UI  | ----> | Cloudflare Edge / CDN |
+-------------------+       +-----------------------+
                                        |
                                        v
                           +--------------------------+
                           | Application Load Balancer|
                           +--------------------------+
                                        |
         +------------------------------+------------------------------+
         |                              |                              |
         v                              v                              v
+------------------+           +------------------+           +------------------+
| FastAPI Instance |           | FastAPI Instance |           | FastAPI Instance |
+------------------+           +------------------+           +------------------+
         |                              |                              |
         +------------------------------+------------------------------+
                                        |
                                        v
                 +----------------------------------------------+
                 | Redis Cluster                                |
                 |  - Fast Result Cache & Rate Limiting         |
                 |  - Task Message Queue (Celery Broker)        |
                 +----------------------------------------------+
                                        |
         +------------------------------+------------------------------+
         |                              |                              |
         v                              v                              v
+------------------+           +------------------+           +------------------+
| Scraping Worker  |           | Scraping Worker  |           | Scraping Worker  |
+------------------+           +------------------+           +------------------+
         |                              |                              |
         v                              v                              v
+------------------+           +------------------+           +------------------+
| Target Websites  |           | PostgreSQL Database|         | AWS S3 Storage   |
| (External Web)   |           | (Audit History)  |           | (Raw HTML/Logs)  |
+------------------+           +------------------+           +------------------+
```

[End-to-End Data Flow]
1. Request Reception: The user issues POST /api/v1/audit with a target URL.
2. Fast-Path Cache Check: FastAPI checks Redis for an unexpired audit result.
   - Cache Hit: Returns JSON directly (<20ms response time).
   - Cache Miss: Proceed to step 3.
3. Task Enqueueing: The API generates a unique job_id, enqueues the scraping
   task into Redis, and immediately returns HTTP 202 (Accepted) with a polling
   endpoint (/api/v1/tasks/{job_id}).
4. Asynchronous Scraping: An idle Celery worker fetches the task, audits the 
   target URL via HTTPX with strict timeouts (5s connection, 10s execution), and 
   parses HTML via BeautifulSoup4.
5. Result Persistence:
   - Worker writes the audit payload to Redis with a 300-second TTL.
   - Job status updates to SUCCESS.
   - Asynchronous batch write saves historical logs to PostgreSQL and raw HTML to S3.
6. Client Retrieval: Client polls /api/v1/tasks/{job_id} or receives a real-time
   webhook notification upon job completion.


## 2. Technology Decision Record (TDR)

| Component | Chosen Technology | Rejected Technology | Decision Rationale |
| :--- | :--- | :--- | :--- |
| **Broker / Queue** | **Redis (Celery)** | **RabbitMQ** | **Redis** handles both in-memory result caching and task queueing under sub-millisecond latencies, eliminating the need to maintain separate infrastructure components. |
| **Database** | **PostgreSQL** | **MongoDB** | **PostgreSQL** provides ACID compliance, strong relational integrity for user/org models, and native `JSONB` support for schema flexibility without sacrificing consistency. |
| **HTTP Client** | **HTTPX (Async)** | **Requests** | **HTTPX** provides native `async`/`await` support, allowing a single worker process to handle hundreds of concurrent non-blocking outbound requests efficiently. |
| **Web Framework** | **FastAPI** | **Django / Flask** | High asynchronous throughput built on Starlette and Pydantic, minimal memory footprint, and native OpenAPI/Swagger documentation generation out of the box. |

> **Key Architectural Takeaway:** The tech stack prioritizes low-latency asynchronous operations (`FastAPI` + `HTTPX`) combined with unified caching/queueing infrastructure (`Redis`) to maximize throughput while minimizing operational complexity.

# 3. FAILURE MODE ANALYSIS (FMA)

## Failure Mode 1: Target Site Latency & "Slow responses " Connection Hangups
- Description: Target websites hang, respond very slowly, or block IP addresses.
- Impact: Worker pool starvation and queue backing up.
- Mitigation Strategy:
  * Strict connection (5s) and read timeouts (10s) on all outbound requests.
  * Outbound rate limiting per domain via Redis locks to prevent IP bans.
  * Integration with a residential proxy pool to rotate request IPs.

## Failure Mode 2: Queue Congestion during 500 Concurrent Request Bursts
- Description: Heavy traffic spikes saturate queue capacity and increase wait times.
- Impact: Increased task latency and violation of user SLAs.
- Mitigation Strategy:
  * Autoscaling workers based on queue length (e.g., KEDA scaling 1 worker 
    per 20 pending items).
  * Dead Letter Queue (DLQ) routing for failing or retried tasks to prevent 
    head-of-line blocking.

## Failure Mode 3: Database Connection Exhaustion
- Description: High worker autoscale count opens too many concurrent connections to PostgreSQL.
- Impact: HTTP 500 errors across API due to DB connection drops.
- Mitigation Strategy:
  * Deploy PgBouncer as a database proxy for connection pooling.
  * Workers write audit results to Redis first, executing non-blocking bulk 
    writes to PostgreSQL.


# 4. OBSERVABILITY, ALERTING & ROLLBACK STRATEGY

## -[Observability Metrics & SLIs/SLOs]
- Latency SLO: 95% of cached API queries served <50ms; async audits completed <5s.
- Error SLO: Maintain <0.1% HTTP 5xx error rate.
- Metric Stack: Prometheus (metrics collection) + Grafana (dashboards) + 
  OpenTelemetry (distributed request tracing with X-Request-ID).

## -[Automated Alerting Triggers]
- Critical Alert: HTTP 5xx errors exceed 2% over a 5-minute rolling window.
- Warning Alert: Celery pending queue depth exceeds 200 tasks for >2 minutes.
- Infra Alert: Redis memory consumption exceeds 85% threshold.

## -[Zero-Downtime Deployment & Rollback Protocol]
- Strategy: Rolling Blue/Green deployment on Kubernetes or AWS ECS.
- Automated Canary Validation:
  1. Route 10% of production traffic to the newly deployed container version.
  2. Monitor error rates and latency metrics automatically for 5 minutes.
  3. If HTTP 5xx errors increase by >0.5% or health checks fail, traffic automatically 
     switches 100% back to the previous stable revision.
- Schema Migrations: Database updates follow the Expand/Contract pattern to maintain 
  backward compatibility with active running containers during rollbacks.

## Note-
Built for Digital Heroes Training Task
