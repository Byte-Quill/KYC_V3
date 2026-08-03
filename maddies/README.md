# Maddies — Workforce Management

A full-stack platform to manage multiple maddies (maids / domestic staff) with a
role-based hierarchy and a dedicated dashboard for every role's workspace.

## Roles & dashboards

| Role           | Dashboard scope | What they see & do                                                                 |
| -------------- | --------------- | ---------------------------------------------------------------------------------- |
| **CEO**        | Organization    | Org-wide stats (users, maddies, assignments, revenue estimate), full activity feed |
| **Superadmin** | Operations      | Operational stats, maddies-by-status breakdown, activity feed                      |
| **Admin**      | Team            | Their own maddies, team members, active assignments; manages maddies & assignments |
| **Employee**   | Workspace       | Their own tasks (kanban) and active assignments                                    |

Hierarchy: `CEO > Superadmin > Admin > Employee`. A user can only create/manage
accounts **strictly below** their own rank, enforced server-side.

## Stack

- **Backend:** Django 5 + Django REST Framework + SimpleJWT
- **Database:** SQLite (dev) — Postgres-ready via `DATABASE_URL`
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS
- **Version control:** Git (commit after each step)

## Project layout

```
maddies/
  backend/    Django project (config) + core app
  frontend/   React + TS + Tailwind SPA
```

## Quick start

### Backend (port 8001)

```bash
cd maddies/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo        # demo users + sample data
python manage.py runserver 127.0.0.1:8001
```

### Frontend (port 5174)

```bash
cd maddies/frontend
npm install
npm run dev                      # http://localhost:5174 (proxies /api → 8001)
```

### Demo accounts

| Role       | Email                    | Password     |
| ---------- | ------------------------ | ------------ |
| CEO        | ceo@maddies.local        | Ceo@12345    |
| Superadmin | superadmin@maddies.local | Super@12345  |
| Admin      | admin@maddies.local      | Admin@12345  |
| Employee   | employee@maddies.local   | Employee@123 |

## API overview

| Endpoint                     | Description                             |
| ---------------------------- | --------------------------------------- |
| `POST /api/auth/token/`      | Login (email + password → JWT)          |
| `GET /api/auth/me/`          | Current user                            |
| `GET /api/dashboard/`        | Role-aware dashboard payload            |
| `GET/POST /api/users/`       | Team management (rank-restricted)       |
| `GET/POST /api/maddies/`     | Maddie CRUD (admin+)                    |
| `GET/POST /api/assignments/` | Assignment CRUD + `POST /:id/complete/` |
| `GET/POST /api/tasks/`       | Task CRUD + `POST /:id/advance/`        |
| `GET /api/activity/`         | Audit feed (scoped by role)             |

## Tests

```bash
cd maddies/backend
python manage.py test core      # 10 tests
```
