# Security Roadmap for Production Scaling

This document outlines security improvements for scaling the Curvature API and web interface to support a larger user base.

## Current Security Model (MVP - Completed ✅)

**What we have now:**
- API keys stored in `api/config.py` (gitignored)
- Keys served via `/config` endpoint
- Frontend loads keys dynamically at runtime
- No secrets committed to git

**Security level:** ✅ Good for development and small deployments
**Suitable for:** Local development, small teams, private deployments

---

## Phase 1: Production Hardening (Before Public Launch)

### 1.1 Environment Variables
**Priority:** HIGH
**Effort:** 1-2 hours

Replace `api/config.py` with environment variables:

```python
# api/server.py
import os
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

if not GOOGLE_MAPS_API_KEY:
    raise ValueError("GOOGLE_MAPS_API_KEY environment variable not set")
```

**Benefits:**
- Industry standard for configuration
- Works with Docker, Kubernetes, cloud platforms
- No config files to manage
- Easier CI/CD integration

**How to deploy:**
```bash
# Development
export GOOGLE_MAPS_API_KEY="your-key-here"
python api/server.py

# Production (systemd)
Environment="GOOGLE_MAPS_API_KEY=your-key"

# Docker
docker run -e GOOGLE_MAPS_API_KEY="your-key" curvature-api
```

### 1.2 API Key Restrictions in Google Cloud
**Priority:** HIGH
**Effort:** 30 minutes

Configure restrictions in [Google Cloud Console](https://console.cloud.google.com/):

1. **HTTP Referrer Restrictions:**
   - `https://yourdomain.com/*`
   - `https://www.yourdomain.com/*`
   - Remove `localhost` in production

2. **API Restrictions:**
   - Only enable "Maps JavaScript API"
   - Disable all other APIs

3. **Quotas & Rate Limiting:**
   - Set daily request limits
   - Enable billing alerts

**Benefits:**
- Prevents unauthorized use if key is compromised
- Limits financial exposure
- Industry best practice

### 1.3 HTTPS Only
**Priority:** HIGH
**Effort:** 2-4 hours

Currently the API runs on HTTP. For production:

```nginx
# nginx config
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
    }
}
```

**Benefits:**
- API keys encrypted in transit
- Required for modern browsers
- Better SEO

**Tools:** Let's Encrypt (free), Certbot

---

## Phase 2: Secrets Management (Medium-Scale)

### 2.1 AWS Secrets Manager / GCP Secret Manager
**Priority:** MEDIUM
**Effort:** 4-6 hours
**Cost:** ~$0.40/secret/month + API calls

For cloud deployments:

```python
# api/server.py with AWS Secrets Manager
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except ClientError as e:
        raise e

secrets = get_secret('curvature/prod/config')
GOOGLE_MAPS_API_KEY = secrets['google_maps_api_key']
```

**Benefits:**
- Centralized secret management
- Automatic rotation support
- Audit logging
- Fine-grained access control
- Encryption at rest

**When to use:** Deploying on AWS, GCP, or Azure

### 2.2 HashiCorp Vault
**Priority:** MEDIUM
**Effort:** 8-12 hours
**Cost:** Free (OSS), Enterprise available

For multi-cloud or on-premise:

```python
import hvac

client = hvac.Client(url='http://vault:8200', token=os.getenv('VAULT_TOKEN'))
secrets = client.secrets.kv.v2.read_secret_version(path='curvature/config')
GOOGLE_MAPS_API_KEY = secrets['data']['data']['google_maps_api_key']
```

**Benefits:**
- Dynamic secrets (time-limited)
- Secret versioning
- Comprehensive audit trail
- Multi-cloud support

**When to use:** Large deployments, compliance requirements, multi-cloud

---

## Phase 3: Advanced Architecture (High-Scale)

### 3.1 Backend Proxy for Maps API
**Priority:** LOW (but better security)
**Effort:** 16-24 hours

Instead of exposing the API key to browsers, proxy all Maps API requests through your backend:

```
Browser → Your API → Google Maps API (with key)
         ↑
    API key never exposed!
```

**Implementation:**

```python
# api/server.py
@app.get("/maps/geocode")
async def proxy_geocode(address: str):
    # Server-side request to Google
    url = f"https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': address,
        'key': GOOGLE_MAPS_API_KEY  # Key never sent to client
    }
    response = requests.get(url, params=params)
    return response.json()
```

**Frontend:**
```javascript
// Browser never sees the API key
const result = await fetch('/maps/geocode?address=Vermont');
```

**Benefits:**
- API key never exposed to browsers
- Full control over rate limiting
- Can add caching layer
- Can aggregate multiple API providers

**Drawbacks:**
- More complex
- Higher server load
- Latency increase
- Still need frontend rendering library

### 3.2 Separate Keys Per Environment
**Priority:** MEDIUM
**Effort:** 1 hour

Different API keys for different environments:

```python
# Automatic based on environment
ENV = os.getenv('ENVIRONMENT', 'development')

KEYS = {
    'development': get_secret('curvature/dev/maps_key'),
    'staging': get_secret('curvature/staging/maps_key'),
    'production': get_secret('curvature/prod/maps_key'),
}

GOOGLE_MAPS_API_KEY = KEYS[ENV]
```

**Benefits:**
- Isolate environments
- Better tracking/monitoring
- Can revoke dev keys without affecting prod
- Different quota limits per environment

### 3.3 User Authentication & Rate Limiting
**Priority:** HIGH for public launch
**Effort:** 20-40 hours

Add user accounts and per-user rate limiting:

```python
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/config")
async def get_config(token: str = Depends(oauth2_scheme)):
    user = verify_token(token)

    # Rate limit check
    if user.requests_today > user.quota:
        raise HTTPException(429, "Rate limit exceeded")

    return {
        "google_maps_api_key": GOOGLE_MAPS_API_KEY,
        "quota_remaining": user.quota - user.requests_today
    }
```

**Benefits:**
- Prevent abuse
- Track usage per user
- Monetization options
- Better analytics

---

## Phase 4: Claude AI Integration Security

### 4.1 Anthropic API Key Management
**Priority:** HIGH (when implementing)
**Effort:** 2-4 hours

When adding Claude for natural language queries:

```python
# NEVER expose Claude API key to frontend!
# Always call from backend

from anthropic import Anthropic

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')  # Or secrets manager
client = Anthropic(api_key=ANTHROPIC_API_KEY)

@app.post("/chat")
async def chat(message: str, user: User = Depends(get_current_user)):
    # Server-side Claude API call
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": message}]
    )
    return response
```

**Critical:** Claude API keys are MORE sensitive than Maps keys and should NEVER be client-side.

---

## Monitoring & Incident Response

### Setup Alerts For:
- API key usage spikes
- Unauthorized domain access attempts
- Rate limit violations
- Failed authentication attempts
- Cost threshold exceeded

### Tools:
- **Google Cloud Monitoring** - Track Maps API usage
- **Sentry** - Error tracking
- **Datadog/New Relic** - Application monitoring
- **PagerDuty** - Incident alerts

---

## Cost Optimization

### Maps API Costs:
- **Dynamic Maps:** $7 per 1,000 loads
- **Static Maps:** $2 per 1,000 loads
- **Free tier:** $200/month credit = ~28,000 map loads

### Optimization strategies:
1. **Caching:** Cache GeoJSON responses (reduces API calls)
2. **Lazy loading:** Only load map when user interacts
3. **Static maps for thumbnails:** Use cheaper static API
4. **CDN:** Serve static assets from CDN
5. **Server-side rendering:** Pre-render common views

---

## Implementation Priority for Public Launch

**Must Have (Before Launch):**
1. ✅ Environment variables for config
2. ✅ Google Cloud API restrictions
3. ✅ HTTPS with valid certificate
4. ✅ Rate limiting (at least IP-based)
5. ✅ Monitoring & alerts

**Should Have (First Month):**
1. User authentication
2. Secrets manager (AWS/GCP)
3. Separate keys per environment
4. CDN for static assets

**Nice to Have (Future):**
1. Backend proxy for Maps API
2. Advanced rate limiting per user
3. HashiCorp Vault
4. Multi-region deployment

---

## Current vs. Production Comparison

| Feature | Current (MVP) | Production Ready |
|---------|--------------|------------------|
| Key Storage | File (gitignored) | Environment vars / Secrets manager |
| API Restrictions | ⚠️ Manual | ✅ Automated via IaC |
| HTTPS | ❌ HTTP only | ✅ HTTPS with cert |
| Rate Limiting | ❌ None | ✅ Per-user quotas |
| Monitoring | ❌ None | ✅ Full observability |
| User Auth | ❌ Public | ✅ OAuth2 / JWT |
| Cost Controls | ⚠️ Manual | ✅ Automated alerts |
| Key Rotation | ⚠️ Manual | ✅ Automated |
| Audit Logging | ❌ None | ✅ Complete audit trail |

---

## Estimated Costs for Public Deployment

**Assumptions:** 10,000 active users, 50 map loads/user/month

| Service | Monthly Cost |
|---------|-------------|
| Google Maps API | ~$175 (500k loads - $200 credit) |
| AWS EC2 (t3.small) | $15 |
| AWS Secrets Manager | $1 |
| CloudFlare CDN | $0 (free tier) |
| Let's Encrypt SSL | $0 (free) |
| Monitoring (Sentry) | $26 (team plan) |
| **Total** | **~$217/month** |

For 100,000 users: ~$1,750/month (mostly Maps API costs)

---

## Next Steps

**Immediate (This Week):**
1. Create GitHub issue: "Implement environment variable configuration"
2. Document Google Cloud Console restrictions
3. Set up HTTPS with Let's Encrypt

**Short Term (This Month):**
1. Implement basic rate limiting
2. Add monitoring & alerts
3. Set up secrets manager

**Long Term (Next Quarter):**
1. User authentication system
2. Backend proxy architecture
3. Multi-region deployment

---

## Resources

- [Google Maps API Security Best Practices](https://developers.google.com/maps/api-security-best-practices)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [12-Factor App Configuration](https://12factor.net/config)
- [AWS Secrets Manager Guide](https://docs.aws.amazon.com/secretsmanager/)
- [FastAPI Security Tutorial](https://fastapi.tiangolo.com/tutorial/security/)

---

**Document Version:** 1.0
**Last Updated:** 2024-12-03
**Authors:** George Smith-Sweeper, Claude (Anthropic AI)
