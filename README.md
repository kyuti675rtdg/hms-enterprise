# HMS Enterprise — Hospital Management System

A full-featured, enterprise-style hospital management system built with
**Django 5 + PostgreSQL**, server-rendered templates, and a hand-written
design system (no CDN dependencies).

## Modules

| Module | URL | What it does |
|---|---|---|
| Dashboard | `/` | KPI cards, today's appointments, low-stock alerts, 14-day revenue chart, recent invoices |
| Patients | `/patients/` | Registration, full-text search (PostgreSQL), detail timeline |
| Appointments | `/appointments/` | Booking with slot conflict prevention, status workflow |
| Doctors | `/doctors/` | CRUD (admin), specializations, fees |
| Medical Records | `/clinical/records/` | Diagnoses, prescriptions, visit notes |
| Pharmacy | `/pharmacy/` | Inventory, low-stock/expiry flags, dispense → auto-invoice |
| Laboratory | `/lab/` | Test catalog, orders, result entry |
| Billing | `/billing/` | Invoices with line items, payments, printable receipts, aging |
| Wards & Beds | `/wards/` | Bed board, admit/discharge |
| Reports | `/reports/` | Revenue, appointments per doctor, top medicines, CSV exports |
| Audit Log | `/audit/` | Every create/update/delete with actor + field diffs (admin) |
| Users | `/accounts/users/` | Role-based accounts (admin) |

Roles: `admin`, `doctor`, `receptionist`, `pharmacist`, `labtech` — every view
is gated; wrong-role access returns 403.

## Run locally

```bash
cd hms-enterprise
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# PostgreSQL (Ubuntu/Debian)
sudo apt-get install -y postgresql
sudo service postgresql start
sudo su postgres -c "psql -c \"CREATE ROLE hms LOGIN PASSWORD 'hms_dev_pw' CREATEDB;\""
sudo su postgres -c "createdb -O hms hmsdb"

cp .env.example .env   # adjust SECRET_KEY / DATABASE_URL as needed
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open http://127.0.0.1:8000.

### Demo logins

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | full access |
| `doctor1` | `doc123` | clinical |
| `recep` | `recep123` | front desk + billing |
| `pharm` | `pharm123` | pharmacy |
| `lab` | `lab123` | laboratory |

## Run with Docker

```bash
docker compose up --build
```

This starts PostgreSQL 16 and the Django app (migrations + gunicorn +
WhiteNoise static files) on http://localhost:8000. Seed demo data first:

```bash
docker compose exec web python manage.py seed_demo
```

Set `SECRET_KEY` and `ALLOWED_HOSTS` in your environment before deploying.

## Tests

```bash
python manage.py test
```

Covers: auth gates (anonymous → login, wrong role → 403), patient CRUD +
full-text search, appointment double-booking (DB constraint), atomic
dispense + auto-invoice, over-dispense blocked, payments + overpay blocked,
admit/discharge bed transitions, audit events with diffs, CSV exports.

## PostgreSQL-specific features

- Patient search via `SearchVector` / `SearchRank`
- Double-booking prevention via partial `UniqueConstraint`
  (`no_double_booking`) + friendly form errors
- `JSONField` diffs on audit events

## Production notes

- `DEBUG=0` enables `SECURE_SSL_REDIRECT`, HSTS, and secure cookies.
- Never commit `.env`; start from `.env.example`.
- This is a functional enterprise-style build, not a certified medical
  device: review data-retention, backup, and access policies before
  handling real patient data.

## After a machine restart

Running processes (PostgreSQL, the dev server) do not survive a machine
restart, but all data and code do. To bring everything back:

```bash
cd ~/workspace/hms-enterprise
./start.sh
```

This starts the embedded PostgreSQL (data lives in `.pgdata/`) and then the
Django dev server on http://127.0.0.1:8000. No re-install or re-seed needed.

## Deploy to internet hosting (Render, free)

`render.yaml` is a ready Blueprint: free Python web service + free
PostgreSQL 16 in Frankfurt. No code changes needed.

1. **Put the code on GitHub.** Create a new repo (public or private),
   then from this folder:
   ```bash
   git remote add origin git@github.com:<you>/<repo>.git   # or the https URL
   git push -u origin master
   ```
2. **Render Dashboard → New → Blueprint** → connect and select the repo
   → Apply. Render reads `render.yaml` and creates `hms-enterprise`
   (web) + `hms-db` (Postgres) with `SECRET_KEY` generated automatically.
   No credit card needed.
3. **Wait for both resources to show Live** — first build takes 5–15 min.
4. **ONCE ONLY:** open the web service → **Shell** tab → run
   `python manage.py seed_demo`. This creates the demo logins
   (admin/admin123, doctor1/doc123, recep/recep123, pharm/pharm123,
   lab/lab123). Do **not** run it again — it clears the demo tables first
   and would wipe real data.
5. Open the service URL (e.g. `https://hms-enterprise.onrender.com`)
   and log in.

### Free-tier reality (checked 2026-10-12)

- Web service **sleeps after ~15 min idle**; first request after that takes
  ~30–60s to wake. Fine for demos/evaluation.
- Free PostgreSQL **expires 30 days after creation**; you get a 14-day
  grace period to upgrade, then the data is deleted. **Upgrade to paid
  (~$7/mo) before putting anything you care about in it.** Free Postgres
  has no backups.
- If the free database is a problem, an alternative is a free
  [Neon](https://neon.com) Postgres (no 30-day expiry) wired in as an
  external `DATABASE_URL` env var — ask before switching.
