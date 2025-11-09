# URL Shortener Service

A production-ready, high-performance URL shortener service built with FastAPI, PostgreSQL, and Redis. Achieves <10ms redirect latency through aggressive caching.

## Features

✅ Shorten long URLs with unique codes (max 10 characters)
✅ Idempotent URL creation (same URL returns same code)
✅ Sub-10ms redirect performance with Redis caching
✅ Rate limiting (100 requests/minute per IP)
✅ Click tracking and analytics
✅ Custom alias support
✅ Admin dashboard with authentication
✅ Pagination for URL listing
✅ Docker containerization with Alpine Linux
✅ Multi-stage Docker builds for minimal image size
✅ 5-year URL retention
✅ Graceful shutdown and error handling

## Architecture

┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│ Client      │────▶│ FastAPI     │────▶│ PostgreSQL   │
└─────────────┘     │ (Alpine)    │     └──────────────┘
                    └─────────────┘              │
                            │                    │
                            ▼                    │
                    ┌─────────────┐              │
                    │ Redis       │◀─────────────┘
                    │ (Cache)     │
                    └─────────────┘

### Tech Stack

- **Backend**: FastAPI (Python 3.12)
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Container**: Docker + Docker Compose
- **Base Image**: Alpine Linux (minimal footprint)

## Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Installation

1. Clone the repository:
   git clone <repository-url>
   cd url_shortener

2. Create `.env` file:
   cp .env.example .env
3. Start the service:
   docker-compose up --build

The service will be available at `http://localhost:8080`

## API Documentation

### Base URL
http://localhost:8080

### Endpoints

#### 1. Create Short URL
curl -X POST http://localhost:8080/api/shorten
-H "Content-Type: application/json"
-d '{"target_url": "https://www.example.com/very/long/url"}'

**Response:**
{
"short_code": "abc123",
"short_url": "http://localhost:8080/abc123",
"original_url": "https://www.example.com/very/long/url",
"created_at": "2025-11-08T18:30:00Z"
}

#### 2. Create Short URL with Custom Alias
curl -X POST http://localhost:8080/api/shorten
-H "Content-Type: application/json"
-d '{"target_url": "https://example.com", "custom_alias": "mylink"}'

#### 3. Redirect to Original URL
curl -L http://localhost:8080/abc123

Redirects to original URL with 301 status

#### 4. Get URL Info
curl http://localhost:8080/api/info/abc123

**Response:**
{
"short_code": "abc123",
"short_url": "http://localhost:8080/abc123",
"original_url": "https://www.example.com/very/long/url",
"click_count": 42,
"last_accessed_at": "2025-11-08T18:35:00Z",
"created_at": "2025-11-08T18:30:00Z",
"is_active": true
}
#### 5. List All URLs (Admin)

curl http://localhost:8080/api/admin/urls?page=1&page_size=20
-H "Authorization: Bearer your_admin_token"

#### 6. Get Analytics (Admin)

curl http://localhost:8080/api/admin/analytics
-H "Authorization: Bearer your_admin_token"

**Response:**
{
"total_urls": 1523,
"total_clicks": 45230,
"active_urls": 1500,
"clicks_today": 892
}

#### 7. Delete URL (Admin)
curl -X DELETE http://localhost:8080/api/admin/urls/abc123
-H "Authorization: Bearer your_admin_token"


## Performance Characteristics

- **Redirect Latency**: <10ms (with Redis cache hit)
- **Throughput**: 10,000+ URLs/day
- **Cache Hit Rate**: >95% for popular URLs
- **Database**: Connection pooling (20 base + 40 overflow)
- **Workers**: 4 Uvicorn workers
- **Rate Limit**: 100 requests/minute per IP

## Design Decisions

### 1. Base62 Encoding
Uses Base62 (A-Z, a-z, 0-9) for compact, URL-safe short codes. Combines auto-increment IDs with MD5 hashing for uniqueness and collision resistance.

### 2. Redis Caching Strategy
- **Write-through**: Cache populated on URL creation
- **TTL**: 24-hour default (configurable)
- **Eviction**: LRU policy with 256MB limit
- **Performance**: Sub-millisecond lookups

### 3. Database Design
- **Indexes**: Hash index on original_url, B-tree on short_code
- **Soft Deletes**: URLs marked inactive instead of deletion
- **Connection Pooling**: asyncpg with 20-60 connections

### 4. Rate Limiting
Token bucket algorithm using Redis with sliding window. Per-IP tracking prevents abuse.

### 5. Idempotency
Duplicate URLs return existing short code via database lookup before creation.

## Production Deployment

### Build and Tag Image
docker build -t your-dockerhub-username/url-shortener:latest .
docker push your-dockerhub-username/url-shortener:latest

### Environment Variables
Critical production settings:
ENV_NAME=production
BASE_URL=https://yourdomain.com
POSTGRES_PASSWORD=<strong-password>
ADMIN_TOKEN=<strong-token>
REDIS_TTL=86400


### Scaling
- Horizontal: Add more app containers behind load balancer
- Database: Read replicas for analytics queries
- Cache: Redis Cluster for distributed caching

## Monitoring

### Health Checks
curl http://localhost:8080/health

### Docker Health Status
docker ps # Check container health status

### Logs
docker-compose logs -f app

## Testing
pip install pytest pytest-asyncio httpx
Run tests
pytest tests/


## Trade-offs

1. **Cache TTL vs Consistency**: 1-hour TTL balances performance and storage. Stale data possible but acceptable for URL redirects.

2. **Soft Deletes**: Enables audit trail and recovery but increases database size.

3. **Base62 vs UUID**: Base62 shorter but requires sequential ID generation. UUID would eliminate collisions but produce longer codes.

4. **Async Everything**: Higher complexity but essential for I/O-bound operations and performance targets.

## License

MIT License

## Support

For issues and questions, please open a GitHub issue.



