# KYC-V3 — Application Verification System

A full-stack KYC (Know Your Customer) / application verification system.

## Stack

- **Backend:** Django 5 + Django REST Framework, JWT auth
- **Database:** PostgreSQL via Supabase (SQLite fallback for zero-config dev)
- **Platform:** Supabase — Postgres, Auth, Storage, Realtime, Edge Functions, pgvector
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS
- **Version control:** Git (commit after each step)

## Features

- User registration & JWT login with roles (Applicant, Reviewer, Admin)
- KYC application submission (personal info, address, ID details)
- Document upload (ID proof, address proof, selfie)
- Reviewer workflow: approve / reject / request resubmission with notes
- Full audit trail of every status change and action
- Status dashboard for applicants; review queue for reviewers

## Project layout

```
backend/    Django project + kyc app
frontend/   React + TS + Tailwind SPA
supabase/   Edge functions + Supabase setup guide
```

## Quick start

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # fill in Supabase credentials (optional for SQLite dev)
python manage.py migrate
python manage.py seed_demo        # creates demo users + sample data
python manage.py runserver        # http://127.0.0.1:8000
```

### Supabase (Postgres, Storage, Realtime, Edge Functions)

See [supabase/README.md](supabase/README.md) for full setup. In short:

1. Create a Supabase project and copy its URL/keys into `backend/.env`.
2. Set `DATABASE_URL` to the Supabase Postgres connection string.
3. `python manage.py migrate` then `python manage.py migrate_to_postgres` to move existing SQLite data.
4. Enable `vector` extension, create the `kyc-documents` storage bucket, deploy the edge function.

When `DATABASE_URL` is unset the backend falls back to local SQLite, so the app
runs with zero external services for development.

### Frontend

```bash
cd frontend
npm install
npm run dev                       # http://127.0.0.1:5173
```

## Demo accounts (after `seed_demo`)

| Role      | Email              | Password   |
| --------- | ------------------ | ---------- |
| Admin     | admin@kyc.local    | Admin@123  |
| Reviewer  | reviewer@kyc.local | Review@123 |
| Applicant | user@kyc.local     | User@123   |

## API overview

| Method   | Endpoint                          | Description                |
| -------- | --------------------------------- | -------------------------- |
| POST     | /api/auth/register/               | Register applicant         |
| POST     | /api/auth/token/                  | Obtain JWT                 |
| GET      | /api/auth/me/                     | Current user profile       |
| GET/POST | /api/applications/                | List / create applications |
| GET      | /api/applications/{id}/           | Application detail         |
| POST     | /api/applications/{id}/submit/    | Submit for review          |
| POST     | /api/applications/{id}/documents/ | Upload document            |
| POST     | /api/applications/{id}/review/    | Reviewer decision          |
| GET      | /api/applications/{id}/audit/     | Audit trail                |
