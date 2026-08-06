# Supabase setup for KYC-V3

This project uses Supabase for the managed Postgres database and file storage.

## 1. Create a project

1. Go to https://supabase.com and create a new project.
2. Note the **Project URL** and **service_role key** from
   *Project Settings → API*.
3. Note the **Postgres connection string** from *Project Settings → Database*.

## 2. Configure the backend

Copy `backend/.env.example` to `backend/.env` and fill in:

```bash
DATABASE_URL=postgres://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
SUPABASE_STORAGE_BUCKET=kyc-documents
```

## 3. Run migrations & move existing data

```bash
cd backend
source .venv/bin/activate
python manage.py migrate                     # create tables in Postgres
python manage.py migrate_to_postgres         # copy rows from db.sqlite3
python manage.py seed_demo                   # (optional) demo users
```

## 4. Create the storage bucket

```bash
supabase storage create kyc-documents --public false
```

or via the dashboard: *Storage → New bucket → kyc-documents* (private).

## Feature → Supabase mapping

| Feature | Supabase capability |
| --- | --- |
| Application data | Dedicated Postgres (500 MB) |
| Auth (JWT) | Django JWT |
| Document uploads | File Storage (private bucket, signed URLs) |
| REST API | Django DRF |
