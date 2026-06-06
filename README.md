# 🚦 API Rate Limiter

A **production-ready**, **distributed** API rate limiter built with **Python**, **FastAPI**, and **Redis** — supporting **4 industry-standard algorithms** with atomic Lua scripts.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)

## 🏗️ Supported Algorithms

| Algorithm | Burst Tolerance | Precision | Memory | Best For |
|-----------|:-:|:-:|:-:|---|
| **Fixed Window** | ⚠️ High | ⚠️ Low | ✅ Low | Simple rate limiting |
| **Sliding Window Log** | ✅ None | ✅ High | ⚠️ High | Precise API control |
| **Token Bucket** | ✅ Controlled | ✅ High | ✅ Low | General purpose APIs |
| **Leaky Bucket** | ❌ None | ✅ High | ✅ Low | Constant-rate processing |

## 🚀 Quick Start

### Docker (Recommended)
```bash
git clone https://github.com/YOUR_USERNAME/api-rate-limiter.git
cd api-rate-limiter
cp .env.example .env
docker-compose up -d
# API → http://localhost:8000
# Swagger docs → http://localhost:8000/docs
```

### Local Development
```bash
cp .env.example .env
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
# Start Redis first, then:
python -m app.main
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check (no rate limit) |
| GET | `/api/public` | Public endpoint (default limit) |
| GET | `/api/limited` | Strict limit (5 req / 30s) |
| GET | `/api/test/{algorithm}` | Test specific algorithm |
| GET | `/api/algorithms` | List all algorithms |
| GET | `/docs` | Swagger UI documentation |

## 📊 Response Headers

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1717650000
X-RateLimit-Algorithm: token_bucket
```

## 🧪 Testing

```bash
pytest                              # All tests + coverage
pytest tests/unit                   # Unit tests only
pytest tests/integration            # Integration tests only
pytest --cov=app --cov-report=html  # HTML coverage report
```

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_ALGORITHM` | `token_bucket` | Algorithm to use |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Window size in seconds |
| `RATE_LIMIT_MAX_REQUESTS` | `10` | Max requests per window |
| `REDIS_HOST` | `127.0.0.1` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |

## 🔍 Stress Test

```bash
for i in $(seq 1 15); do
  echo "Request $i: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/public)"
done
# Expected: 200 x10, then 429 x5
```

## 📜 License

MIT © Prashant Singh
