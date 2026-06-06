# ReachGTM — API Reference

Base URL: `http://localhost:8000` (dev) / `https://api.reachgtm.com` (prod)

All protected endpoints require `Authorization: Bearer <access_token>`.

---

## Auth

### POST /api/v1/auth/register
Creates a new company and owner user.

**Auth:** None

**Request:**
```json
{ "email": "string", "password": "string", "company_name": "string" }
```

**Response 201:**
```json
{ "access_token": "string", "refresh_token": "string", "token_type": "bearer", "expires_in": 900 }
```

**Errors:** 400 email already registered

---

### POST /api/v1/auth/login
**Auth:** None

**Request:**
```json
{ "email": "string", "password": "string" }
```

**Response 200:** Same as register

**Errors:** 401 invalid credentials

---

### POST /api/v1/auth/refresh
**Auth:** None

**Request:**
```json
{ "refresh_token": "string" }
```

**Response 200:** New TokenResponse

**Errors:** 401 invalid/expired refresh token

---

### POST /api/v1/auth/invite
**Auth:** Required (owner or admin role)

**Request:**
```json
{ "role": "member" }
```

**Response 200:**
```json
{ "invite_token": "string", "invite_url": "/register?invite=<token>" }
```

---

### POST /api/v1/auth/accept-invite
**Auth:** None

**Request:**
```json
{ "invite_token": "string", "email": "string", "password": "string" }
```

**Response 201:** TokenResponse

**Errors:** 400 invalid/expired invite token

---

## Strategy

### POST /api/v1/strategy/generate
Triggers LangGraph pipeline. Returns immediately; stream events via SSE.

**Auth:** Required

**Request:**
```json
{
  "company_profile": {
    "name": "string", "industry": "string", "stage": "seed|series_a|series_b|growth",
    "description": "string", "website": "string|null", "founded_year": 2020
  },
  "additional_context": "string|null"
}
```

**Response 200:**
```json
{ "session_id": "uuid", "status": "generating" }
```

**SSE stream:** `GET /api/v1/strategy/generate/stream?session_id=<uuid>&token=<jwt>`

Events: `agent_start`, `agent_progress`, `agent_output`, `agent_complete`, `done`, `error`

---

### GET /api/v1/strategy/{strategy_id}
**Auth:** Required

**Response 200:**
```json
{ "id": "uuid", "status": "complete|generating|failed", "payload": { /* GTMStrategy */ }, "created_at": "datetime" }
```

**Errors:** 404 not found, 403 not your company

---

## Content

### POST /api/v1/content/generate
**Auth:** Required

**Request:**
```json
{ "strategy_id": "uuid", "content_types": ["cold_email", "linkedin_post"], "count_per_type": 3 }
```

**Response 200:**
```json
{ "assets": [ /* ContentAsset[] */ ] }
```

---

### GET /api/v1/content/
**Auth:** Required

**Response 200:**
```json
{ "assets": [ /* ContentAsset[] */ ], "total": 0 }
```

---

## Knowledge

### POST /api/v1/knowledge/upload
**Auth:** Required

**Request:** `multipart/form-data`
- `file`: PDF or DOCX file
- `doc_type`: `pitch_deck` | `case_study` | `brand_guide` | `competitor_analysis` | `other`

**Response 200:**
```json
{ "document_id": "uuid", "chunks": 42, "status": "indexed" }
```

**Errors:** 400 unsupported file type, 422 extraction failed

---

### GET /api/v1/knowledge/
**Auth:** Required

**Response 200:**
```json
{ "documents": [ { "id": "uuid", "filename": "string", "doc_type": "string", "status": "indexed", "chunk_count": 42, "created_at": "datetime" } ] }
```

---

## Chat

### POST /api/v1/chat/
**Auth:** Required

**Request:**
```json
{ "session_id": "uuid|null", "message": "string", "company_id": "uuid" }
```

**Response:** SSE stream (Epic 2)

---

## Health

### GET /health
**Auth:** None

**Response 200:**
```json
{ "service": "backend", "status": "ok" }
```
