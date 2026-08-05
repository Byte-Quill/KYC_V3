# KYC-V3 — Application Verification System

A full-stack KYC (Know Your Customer) / application verification system built with Django + React, using Supabase for Postgres, Storage, Realtime, and Edge Functions.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            KYC-V3 SYSTEM ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐         HTTPS/REST          ┌────────────────────────┐   │
│  │   FRONTEND   │ ◄─────────────────────────► │       BACKEND          │   │
│  │  (Vercel)    │                             │      (Render)          │   │
│  │              │   JWT in Authorization      │                        │   │
│  │  React 19    │   Header + Refresh Token    │  Django 5.2 + DRF      │   │
│  │  TypeScript  │                             │  SimpleJWT Auth        │   │
│  │  Vite 6      │   /api/* endpoints          │  WhiteNoise Static     │   │
│  │  Tailwind    │                             │  Gunicorn WSGI         │   │
│  └──────────────┘                             └───────────┬────────────┘   │
│                                                          │                │
│                    ┌─────────────────────────────────────┼────────────┐   │
│                    │              SUPABASE               │            │   │
│                    │  ┌──────────┐ ┌─────────┐ ┌───────┐ │ ┌────────┐ │   │
│                    │  │ Postgres │ │ Storage │ │Realtime│ │ │ Edge   │ │   │
│                    │  │(Pooler)  │ │(Bucket) │ │Broadcast│ │ │Functions│ │   │
│                    │  └──────────┘ └─────────┘ └───────┘ │ └────────┘ │   │
│                    └─────────────────────────────────────┴────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer              | Technology                                 | Purpose                                |
| ------------------ | ------------------------------------------ | -------------------------------------- |
| **Backend**        | Django 5.2, DRF 3.16                       | REST API, business logic               |
| **Auth**           | SimpleJWT (access 1h, refresh 7d)          | Stateless JWT authentication           |
| **Database**       | Supabase Postgres (Transaction Pooler)     | Primary data store                     |
| **File Storage**   | Supabase Storage (`kyc-documents` bucket)  | Document uploads, CDN URLs             |
| **Realtime**       | Supabase Realtime (`kyc-status` channel)   | Live status updates                    |
| **Edge Functions** | Supabase Edge Functions (Deno)             | Embedding generation for vector search |
| **Frontend**       | React 19, TypeScript, Vite 6, Tailwind CSS | SPA, deployed on Vercel                |
| **Deployment**     | Render (backend), Vercel (frontend)        | Free-tier hosting                      |

---

## Project Structure

```
KYC-V3/
├── backend/                    # Django project
│   ├── config/                 # Settings, URLs, WSGI/ASGI
│   │   ├── settings.py         # All configuration (env-driven)
│   │   └── urls.py             # Root URL routing
│   ├── kyc/                    # Main app
│   │   ├── models.py           # User, KYCApplication, Document, AuditLog
│   │   ├── views.py            # ViewSets: Applications, Documents, Review, Audit
│   │   ├── serializers.py      # DRF serializers (Supabase URL for documents)
│   │   ├── permissions.py      # IsApplicant, IsReviewer, IsAdmin, ownership checks
│   │   ├── supabase_client.py  # Thin wrapper: storage, realtime, generic helpers
│   │   ├── management/commands/
│   │   │   ├── seed_demo.py    # Creates demo users + sample data
│   │   │   └── migrate_to_postgres.py  # SQLite → Postgres data migration
│   │   └── migrations/         # 3 migrations (initial, embedding, storage_path)
│   ├── .env                    # Local env (DATABASE_URL, Supabase keys)
│   ├── .env.example            # Template
│   ├── requirements.txt        # Python deps
│   └── manage.py
├── frontend/                   # React SPA
│   ├── src/
│   │   ├── api.ts              # Axios-like fetch wrapper, token refresh, VITE_API_URL
│   │   ├── auth.tsx            # Auth context, login/register forms
│   │   ├── types.ts            # TypeScript interfaces matching backend
│   │   ├── components/         # Reusable UI (Field, Button, Modal, etc.)
│   │   └── pages/              # Route pages (Dashboard, ApplicationForm, ReviewQueue, etc.)
│   ├── vite.config.ts          # Dev proxy to localhost:8000
│   └── package.json
├── supabase/
│   ├── functions/
│   │   └── generate-embedding/ # Edge Function: OpenAI embeddings → pgvector
│   └── README.md               # Supabase setup guide
├── render.yaml                 # Render Blueprint (backend only)
├── Dockerfile                  # Multi-stage (Node + Python) for container deploy
└── README.md                   # This file
```

---

## Data Models & Relationships

```
User (custom, email=USERNAME_FIELD)
  ├── role: APPLICANT | REVIEWER | ADMIN
  └── 1:N KYCApplication (applicant)

KYCApplication
  ├── applicant → User
  ├── status: DRAFT | SUBMITTED | UNDER_REVIEW | APPROVED | REJECTED | RESUBMISSION_REQUESTED
  ├── personal_info (JSON): name, dob, nationality, id_number, id_type
  ├── address_info (JSON): line1, line2, city, state, postal_code, country
  ├── id_details (JSON): document_type, number, expiry, issuing_country
  ├── reviewer → User (nullable)
  ├── reviewed_at, review_notes
  ├── embedding (vector, 1536-dim) — for semantic search
  ├── 1:N Document
  └── 1:N AuditLog

Document
  ├── application → KYCApplication
  ├── doc_type: ID_PROOF | ADDRESS_PROOF | SELFIE
  ├── file (FileField) — local fallback
  ├── storage_path (CharField) — Supabase Storage path when mirrored
  ├── original_filename
  └── uploaded_at

AuditLog
  ├── application → KYCApplication
  ├── actor → User
  ├── action: CREATED | SUBMITTED | DOCUMENT_UPLOADED | REVIEWED | STATUS_CHANGED | ...
  ├── detail (text)
  └── created_at
```

---

## Authentication Flow

```
┌─────────┐     POST /api/auth/register/      ┌─────────┐
│ Frontend │ ─────────────────────────────────► │ Backend │
└─────────┘   {email, password, name, role}    └────┬────┘
                                                     │
                                                     ▼
                                            Create User (role=APPLICANT)
                                            Return 201 + user data
                                                     │
┌─────────┐     POST /api/auth/token/        ◄───────┘
│ Frontend │ ─────────────────────────────────►
└─────────┘   {email, password}              │
                │                            ▼
                │                    Validate credentials
                │                    Return {access, refresh}
                │                            │
                ▼                            │
         Store tokens in memory + localStorage
         Set Authorization: Bearer <access>
                │
                ▼
    ┌─────────────────────────────────────────────────────┐
    │           Subsequent Requests                        │
    │  GET /api/applications/                              │
    │  Authorization: Bearer <access>                      │
    │                                                      │
    │  If 401 (expired):                                   │
    │    POST /api/auth/token/refresh/ {refresh}           │
    │    → new access token, retry original request        │
    └─────────────────────────────────────────────────────┘
```

**Token lifetimes:** Access = 1 hour, Refresh = 7 days (configurable in `SIMPLE_JWT`).

---

## Application Lifecycle (State Machine)

```
DRAFT
  │
  ├─► User fills form (personal, address, ID details)
  │
  ├─► Upload documents (ID_PROOF, ADDRESS_PROOF, SELFIE)
  │     → POST /api/applications/{id}/documents/
  │     → File saved locally + mirrored to Supabase Storage
  │     → Document.storage_path set
  │
  ▼
SUBMITTED          POST /api/applications/{id}/submit/
  │                → Validates required docs present
  │                → Creates AuditLog(SUBMITTED)
  │                → Broadcasts realtime status change
  │
  ▼
UNDER_REVIEW       Reviewer claims from queue
  │
  ├─► APPROVED           POST /api/applications/{id}/review/
  │     {decision: "approve", notes: "..."}
  │     → status = APPROVED, reviewer = current user
  │     → AuditLog(REVIEWED), Broadcast
  │
  ├─► REJECTED           {decision: "reject", notes: "..."}
  │     → status = REJECTED
  │     → AuditLog(REVIEWED), Broadcast
  │
  └─► RESUBMISSION_REQUESTED  {decision: "resubmit", notes: "Missing ID proof"}
        → status = RESUBMISSION_REQUESTED
        → Applicant sees required changes, can edit & re-submit
```

---

## API Endpoints Summary

| Method | Endpoint                                     | Auth | Role                                | Description              |
| ------ | -------------------------------------------- | ---- | ----------------------------------- | ------------------------ |
| POST   | `/api/auth/register/`                        | ❌   | —                                   | Register applicant       |
| POST   | `/api/auth/token/`                           | ❌   | —                                   | Login → JWT pair         |
| POST   | `/api/auth/token/refresh/`                   | ❌   | —                                   | Refresh access token     |
| GET    | `/api/auth/me/`                              | ✅   | Any                                 | Current user profile     |
| GET    | `/api/applications/`                         | ✅   | Applicant: own, Reviewer/Admin: all | List applications        |
| POST   | `/api/applications/`                         | ✅   | Applicant                           | Create draft application |
| GET    | `/api/applications/{id}/`                    | ✅   | Owner/Reviewer/Admin                | Application detail       |
| PATCH  | `/api/applications/{id}/`                    | ✅   | Applicant (DRAFT only)              | Update draft             |
| POST   | `/api/applications/{id}/submit/`             | ✅   | Applicant                           | Submit for review        |
| POST   | `/api/applications/{id}/documents/`          | ✅   | Applicant                           | Upload document          |
| DELETE | `/api/applications/{id}/documents/{doc_id}/` | ✅   | Applicant                           | Delete document          |
| POST   | `/api/applications/{id}/review/`             | ✅   | Reviewer/Admin                      | Approve/Reject/Resubmit  |
| GET    | `/api/applications/{id}/audit/`              | ✅   | Owner/Reviewer/Admin                | Audit trail              |
| GET    | `/api/review/queue/`                         | ✅   | Reviewer/Admin                      | Pending review queue     |

---

## Frontend Pages & Routes

| Route               | Component               | Purpose                                      |
| ------------------- | ----------------------- | -------------------------------------------- |
| `/`                 | `DashboardPage`         | Role-based redirect                          |
| `/login`            | `LoginPage`             | Email/password login                         |
| `/register`         | `RegisterPage`          | New applicant registration                   |
| `/applications`     | `ApplicationListPage`   | My applications (applicant) / All (reviewer) |
| `/applications/new` | `ApplicationFormPage`   | Multi-step form wizard                       |
| `/applications/:id` | `ApplicationDetailPage` | View + upload docs + submit                  |
| `/review`           | `ReviewQueuePage`       | Reviewer queue with filters                  |
| `/review/:id`       | `ReviewDetailPage`      | Review decision modal                        |
| `/profile`          | `ProfilePage`           | User info, logout                            |

---

## Supabase Integration Details

### 1. Database (Postgres via Transaction Pooler)

- **URI format:** `postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres`
- Set as `DATABASE_URL` in Render env vars
- Migrations run on deploy via `startCommand` in `render.yaml`

### 2. Storage (Document Uploads)

- Bucket: `kyc-documents` (create in Supabase Dashboard → Storage)
- **Public bucket** → `get_public_url()` returns CDN URL
- **Private bucket** → use `create_signed_url(path, 3600)` for 1-hour links
- Backend mirrors every upload to Supabase; `Document.storage_path` stores the path
- `DocumentSerializer.get_file()` returns Supabase URL when available, else local

### 3. Realtime (Live Status Updates)

- Channel: `kyc-status`
- Event: `status_changed` → `{application_id, status, detail}`
- Frontend can subscribe (not yet implemented) for live dashboard updates
- `supabase_client.broadcast_status_change()` called on every status transition

### 4. Edge Function (Embeddings)

- Path: `supabase/functions/generate-embedding/`
- Trigger: HTTP POST with `{application_id, text}`
- Calls OpenAI `text-embedding-3-small` → 1536-dim vector
- Upserts into `kyc_application.embedding` (pgvector)
- Enable `vector` extension in Supabase SQL editor: `CREATE EXTENSION vector;`

---

## Local Development

### Prerequisites

- Python 3.11+, Node 18+, Supabase CLI (optional)

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: add DATABASE_URL (Supabase pooler), SUPABASE_* keys
python manage.py migrate
python manage.py seed_demo          # Optional: demo users + data
python manage.py runserver          # http://127.0.0.1:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                         # http://localhost:5173
# Proxies /api/* and /media/* to localhost:8000 via vite.config.ts
```

### Demo Accounts (after `seed_demo`)

| Role      | Email              | Password   |
| --------- | ------------------ | ---------- |
| Admin     | admin@kyc.local    | Admin@123  |
| Reviewer  | reviewer@kyc.local | Review@123 |
| Applicant | user@kyc.local     | User@123   |

---

## Deployment

### Backend → Render (Free Tier)

1. Push repo to GitHub
2. Render Dashboard → **New → Blueprint** → select repo
3. Blueprint reads `render.yaml` (backend service only)
4. **Environment Variables** (set in Render dashboard):
   ```
   DATABASE_URL=postgresql://postgres.<ref>:<pwd>@aws-0-<region>.pooler.supabase.com:6543/postgres
   SUPABASE_URL=https://<ref>.supabase.co
   SUPABASE_ANON_KEY=<anon-key>
   SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
   SUPABASE_STORAGE_BUCKET=kyc-documents
   CORS_ALLOWED_ORIGINS=https://your-app.vercel.app
   DJANGO_CSRF_TRUSTED_ORIGINS=https://your-app.vercel.app
   DJANGO_SECRET_KEY=<auto-generated>
   DJANGO_DEBUG=false
   DJANGO_ALLOWED_HOSTS=.onrender.com
   ```
5. Deploy → URL: `https://kyc-backend.onrender.com`

### Frontend → Vercel

1. Vercel → **Import Project** → same repo
2. **Root Directory**: `frontend`
3. **Framework**: Vite (auto)
4. **Build Command**: `npm run build`
5. **Output Directory**: `dist`
6. **Environment Variable**:
   ```
   VITE_API_URL=https://kyc-backend.onrender.com
   ```
7. Deploy → URL: `https://your-app.vercel.app`

### Supabase Setup Checklist

- [ ] Create project → copy URL, anon key, service role key
- [ ] **Database** → enable `vector` extension (SQL: `CREATE EXTENSION vector;`)
- [ ] **Storage** → create bucket `kyc-documents` (public or private)
- [ ] **Edge Functions** → deploy `generate-embedding` (set `OPENAI_API_KEY` in function env)
- [ ] **Realtime** → enable for `kyc-status` channel (default on)

---

## Key Implementation Details

### Permissions (`kyc/permissions.py`)

- `IsApplicant` — user.role == APPLICANT
- `IsReviewer` — user.role in [REVIEWER, ADMIN]
- `IsAdmin` — user.role == ADMIN
- `IsOwnerOrReviewer` — applicant owns object OR reviewer/admin
- Applied per-viewset via `permission_classes`

### Document Upload Flow (`views.py:upload_document`)

1. Validate file type (jpg, jpeg, png, pdf) & size (≤5MB)
2. Save to local `media/documents/<app_id>/<uuid>.<ext>`
3. If Supabase configured:
   - Read file bytes → `supabase_client.upload_document(path, bytes, content_type)`
   - On success: `document.storage_path = path` → save
4. Return `DocumentSerializer` data (includes Supabase URL via `get_file()`)

### Audit Logging (`views.py:log_action`)

- Called on every state change: create, submit, upload, review, status change
- Records: application, actor, action enum, detail text, timestamp
- Exposed via `/api/applications/{id}/audit/`

### CORS & CSRF (`settings.py`)

- `CORS_ALLOWED_ORIGINS` from env (comma-separated)
- `CSRF_TRUSTED_ORIGINS` from env
- Both support Vercel domain + local dev

---

## Environment Variables Reference

### Backend (`.env` / Render)

| Variable                      | Required | Description                         |
| ----------------------------- | -------- | ----------------------------------- |
| `DJANGO_SECRET_KEY`           | ✅       | 50+ char random string              |
| `DJANGO_DEBUG`                | ✅       | `true`/`false`                      |
| `DJANGO_ALLOWED_HOSTS`        | ✅       | Comma-separated hosts               |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | ✅       | Comma-separated origins (HTTPS)     |
| `DATABASE_URL`                | ✅       | Supabase Postgres pooler URI        |
| `SUPABASE_URL`                | ✅       | `https://<ref>.supabase.co`         |
| `SUPABASE_ANON_KEY`           | ✅       | Public anon key                     |
| `SUPABASE_SERVICE_ROLE_KEY`   | ✅       | Secret service role key             |
| `SUPABASE_STORAGE_BUCKET`     | ✅       | Bucket name (e.g., `kyc-documents`) |
| `CORS_ALLOWED_ORIGINS`        | ✅       | Frontend URL(s) for CORS            |
| `CUSTOM_DOMAIN`               | ❌       | Optional custom domain for CORS     |

### Frontend (Vercel)

| Variable       | Required | Description                                                 |
| -------------- | -------- | ----------------------------------------------------------- |
| `VITE_API_URL` | ✅       | Backend base URL (e.g., `https://kyc-backend.onrender.com`) |

---

## Common Commands

```bash
# Backend
cd backend && source .venv/bin/activate
python manage.py migrate              # Apply migrations
python manage.py makemigrations kyc   # Create new migration
python manage.py seed_demo            # Seed demo data
python manage.py migrate_to_postgres  # Migrate SQLite → Postgres
python manage.py test kyc.tests       # Run tests (8 tests)
python manage.py createsuperuser      # Create admin user

# Frontend
cd frontend
npm run dev                           # Dev server
npm run build                         # Production build
npm run preview                       # Preview build locally

# Supabase CLI (optional)
supabase login
supabase link --project-ref <ref>
supabase db push                      # Push migrations
supabase functions deploy generate-embedding
```

---

## Troubleshooting

| Issue                                    | Cause                      | Fix                                                                                         |
| ---------------------------------------- | -------------------------- | ------------------------------------------------------------------------------------------- |
| `ENOTFOUND` / `ENOIDENTIFIER` on migrate | Wrong pooler URI           | Use **Transaction Pooler** (port 6543) with `postgres.<ref>` user                           |
| CORS error on Vercel                     | Missing origin in backend  | Add `https://your-app.vercel.app` to `CORS_ALLOWED_ORIGINS` & `DJANGO_CSRF_TRUSTED_ORIGINS` |
| 401 after refresh                        | Refresh token expired (7d) | Re-login; check `SIMPLE_JWT.REFRESH_TOKEN_LIFETIME`                                         |
| Documents not showing                    | Supabase bucket private    | Use signed URLs or make bucket public                                                       |
| Realtime not working                     | Channel not subscribed     | Frontend needs to implement `supabase.channel('kyc-status').on('broadcast', ...)`           |
| Render deploy fails                      | `DATABASE_URL` not set     | Add all env vars in Render dashboard before deploy                                          |

---

## License

MIT — free to use, modify, distribute.
