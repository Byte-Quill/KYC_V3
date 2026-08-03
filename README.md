# KYC-V3 — Application Verification System

A full-stack KYC (Know Your Customer) / application verification system.

## Stack

- **Backend:** Django 5 + Django REST Framework, JWT auth, SQLite (dev)
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
```

## Quick start

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo        # creates demo users + sample data
python manage.py runserver        # http://127.0.0.1:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                       # http://127.0.0.1:5173
```

## Demo accounts (after `seed_demo`)

| Role      | Email               | Password    |
|-----------|---------------------|-------------|
| Admin     | admin@kyc.local     | Admin@123   |
| Reviewer  | reviewer@kyc.local  | Review@123  |
| Applicant | user@kyc.local      | User@123    |

## API overview

| Method | Endpoint                          | Description                  |
|--------|-----------------------------------|------------------------------|
| POST   | /api/auth/register/               | Register applicant           |
| POST   | /api/auth/token/                  | Obtain JWT                   |
| GET    | /api/auth/me/                     | Current user profile         |
| GET/POST | /api/applications/              | List / create applications   |
| GET    | /api/applications/{id}/           | Application detail           |
| POST   | /api/applications/{id}/submit/    | Submit for review            |
| POST   | /api/applications/{id}/documents/ | Upload document              |
| POST   | /api/applications/{id}/review/    | Reviewer decision            |
| GET    | /api/applications/{id}/audit/     | Audit trail                  |
