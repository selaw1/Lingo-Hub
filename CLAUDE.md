# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Lingo Hub** is a Django QR attendance + loyalty system for teachers and students:
- Teachers create sessions and display QR codes for students to scan
- Students scan QR codes to record attendance and earn loyalty stamps
- Stamps accumulate toward tiers (Bronze/Silver/Gold/etc)
- Students can view their stamp count, current tier, and progress on their Lingo Card (the home page)
- Hosts and admins can create sessions, view session attendees, and export a session's attendance to Excel

## Architecture (Locked In)

**Full Django monolith — no SPA, no separate frontend, no JWT.**

Key reasoning:
- Scan → verify → write to DB → render updated page is fundamentally server-side
- Session auth + `@login_required` is simpler and safer than JWT/CORS complexity
- PostgreSQL is the single source of truth; every page renders fresh per-request
- Optional future UI polish (stamp animations, better interactivity) should use htmx or Alpine.js on top of Django templates, NOT a full SPA

**Tech Stack:**
- Django (sessions auth only)
- PostgreSQL (ALWAYS, no SQLite)
- Django templates (no React, no separate frontend)
- Tailwind CDN only
- html5-qrcode for QR scanning
- PWA (manifest + service worker) for home-screen install instead of Apple/Google Wallet (simpler, no paid developer accounts needed)

## Development Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install django psycopg2-binary pandas openpyxl django-ratelimit

# Database
python manage.py migrate

# Dev server
python manage.py runserver

# Create a superuser (admin)
python manage.py createsuperuser

# Add initial tiers via Django shell (one-time)
python manage.py shell
>>> from loyalty.models import Tier
>>> Tier.objects.create(name="Bronze", min_stamps=0, order=1)
>>> Tier.objects.create(name="Silver", min_stamps=10, order=2)
>>> Tier.objects.create(name="Gold", min_stamps=25, order=3)
```

## Project Structure

```
core/               # Django project settings
├── settings.py    # PostgreSQL config ONLY; see DATABASES section below
├── urls.py
└── wsgi.py

accounts/          # User registration/login (minimal; uses Django's built-in User)
sessions/          # Teacher creates sessions with QR codes
├── models.py      # Session
└── views.py

attendance/        # QR scanning and attendance recording
├── models.py      # Attendance
├── views.py       # scan_view (POST endpoint), session_attendees_view (admin only)
└── urls.py

loyalty/           # Stamps, tiers, and wallet
├── models.py      # Tier, Stamp
├── views.py       # wallet_view, export_view
├── utils.py       # get_user_tier(user) — derives current tier from stamp count
└── urls.py

templates/         # Django templates (Tailwind CDN)
├── base.html
├── sessions/
├── attendance/
└── loyalty/

static/            # Tailwind CDN link in base.html, manifest.json, sw.js
```

## Key Models

### Session (sessions/models.py)
- `title`: session name
- `created_by`: FK to User
- `created_at`: auto timestamp
- `is_active`: boolean, allows deactivating sessions

### Attendance (attendance/models.py)
- `user` + `session` are **unique together** — prevents duplicate scans
- `timestamp`: auto timestamp
- Links students to the sessions they scanned into

### Stamp (loyalty/models.py)
- **Decoupled from Attendance intentionally** — allows bonus stamps (events, manual awards, streaks) without DB changes
- `source`: "attendance", "event", "manual", "streak"
- `user`: ForeignKey
- `attendance`: nullable ForeignKey (attendance stamps link here; event/manual leave it blank)
- `awarded_by`: nullable FK to User (who gave the stamp, if manual)
- `created_at`: auto timestamp

### Tier (loyalty/models.py)
- `name`: Bronze, Silver, Gold, etc.
- `min_stamps`: threshold to reach this tier
- `icon`: emoji or static path
- `order`: display order
- **Tier is derived, never stored on User** — always calculate from `Stamp.objects.filter(user=user).count()`

## Critical Implementation Details

### QR System
- Use `TimestampSigner` from `django.core.signing`
- QR codes expire in **3 minutes** (`max_age=180`)
- Teacher's QR display should refresh every 30–60 seconds to keep old screenshots stale
- Signed format: `signer.sign(session_id)` → can be embedded in QR
- Validation: `signer.unsign(qr, max_age=180)` raises `BadSignature` or `SignatureExpired`

### Scan Endpoint (attendance/views.py)
```python
def scan_view(request):
    qr = request.POST.get("qr")
    try:
        session_id = signer.unsign(qr, max_age=180)
    except (BadSignature, SignatureExpired):
        return redirect("scan_error")
    
    session = get_object_or_404(Session, id=session_id, is_active=True)
    attendance, created = Attendance.objects.get_or_create(
        user=request.user, session=session
    )
    if created:  # IMPORTANT: guard prevents duplicate stamp awards
        Stamp.objects.create(user=request.user, source="attendance", attendance=attendance)
    
    return redirect("wallet")
```
**Key:** `if created` guard is essential — `unique_together` blocks duplicate Attendance, but without the guard a second POST would still try to create a second Stamp.

### Tier Derivation (loyalty/utils.py)
```python
def get_user_tier(user):
    stamp_count = Stamp.objects.filter(user=user).count()
    tier = Tier.objects.filter(min_stamps__lte=stamp_count).order_by("-min_stamps").first()
    return tier, stamp_count
```
Tier is never stored on the user model — it's always calculated from current stamp count. This allows changing tier thresholds without data migration.

### Session Attendees View (hosts + admins)
- Restricted via `@host_or_admin_required` (`common/decorators.py`): `is_staff` OR `user_type == "host"`
- **Not** based on session ownership
- Path: `/attendance/sessions/<session_id>/attendees/`

### Lingo Card / Home Page (loyalty/views.py, at `/`)
- The wallet is called the **Lingo Card** in the UI and is the home page
- No navbar — the home page contains navigable sections instead
- Shows total stamps, current tier, next-tier progress, and tier ladder
- Uses `get_user_tier()` helper to derive current state

### Excel Export (per-session only, hosts + admins)
- Export only exists *within* a session: `/attendance/sessions/<session_id>/attendees/export/`
- There is deliberately **no global export** endpoint
- Gated by `@host_or_admin_required`; implemented in `attendance/views.py` with pandas `to_excel` (strip tzinfo — Excel rejects tz-aware datetimes)

### Student Permissions
- Students can only join sessions (scan) — they cannot create sessions, view attendees, or export
- Students can be in **one active session at a time**: the scan endpoint blocks a student who already has an Attendance in another `is_active=True` session (re-scanning the same session stays idempotent)

## Settings & Config

### settings.py — PostgreSQL Config (LOCKED IN)
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "your_db",
        "USER": "your_user",
        "PASSWORD": "your_password",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```
**No SQLite. Ever.** PostgreSQL is non-negotiable.

### INSTALLED_APPS
```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "sessions",
    "attendance",
    "loyalty",
]
```

## Rules (Locked In)

1. **PostgreSQL ONLY** — no SQLite, no other database
2. **Full Django monolith** — no React, no SPA, no separate frontend
3. **Sessions auth only** — no JWT, no token refresh complexity
4. **QR codes must be time-limited** — `TimestampSigner` with `max_age`, not permanently valid
5. **Stamps are separate from Attendance** — allows bonus stamps without schema changes
6. **Tier is derived, never stored** — always calculate from stamp count
7. **Session management (list/create/QR/attendees) and export are `@host_or_admin_required`** — `is_staff` or `user_type == "host"`, not ownership-based; students only join sessions
8. **django-ratelimit** on the scan endpoint — prevents brute-force QR hammering
9. **PWA for wallet install** — manifest.json + service worker, no Apple/Google Wallet API setup needed

## Future Enhancements (Optional)

- Add htmx or Alpine.js for UI polish (stamp animations, real-time updates) without changing architecture
- Implement streak bonuses (bonus stamps for scanning X sessions in a row)
- Add event-based stamp awards (teacher creates "bonus event", students can earn stamps)
- Cache tier lookups if staff users report slow wallet page loads
- Implement service worker offline caching for PWA (currently just makes it installable, not offline-functional)

## Deployment

Use PostgreSQL in production. Works on Clever Cloud, Render, or any VPS.

### Free hosting: Render (web) + Neon or Supabase (Postgres)

Render's own free Postgres expires after 30 days; pairing Render's free web
service with a separate always-free Postgres (Neon or Supabase) avoids that.

**One-time setup:**
1. Create a free Postgres database on [Neon](https://neon.tech) or
   [Supabase](https://supabase.com). Either gives you a connection string —
   pull `host`, `port` (usually `5432`), `database name`, `user`, and
   `password` out of it.
2. On [Render](https://render.com), create a new **Blueprint** from this
   repo — it reads `render.yaml` at the repo root and creates the web
   service, build command (`pip install`, `collectstatic`, `migrate`), and
   start command (`gunicorn core.wsgi:application`) automatically.
3. In the Render dashboard, set the env vars `render.yaml` marks
   `sync: false` (not committed to the repo):
   - `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` — from step 1
   - `DJANGO_ALLOWED_HOSTS` — your `*.onrender.com` hostname (Render also
     auto-appends `RENDER_EXTERNAL_HOSTNAME` to `ALLOWED_HOSTS`, so this can
     stay blank)
   - `DJANGO_SECRET_KEY` — `render.yaml` generates one automatically; only
     set this yourself if you want to control the value
4. Deploy. Then create tiers and a superuser once, from Render's shell tab
   (or locally, pointed at the same DB via those same `DB_*` vars):
   `python manage.py createsuperuser`.

**Alternative:** `core/settings.py` also accepts a single `DATABASE_URL`
connection string (checked first, before the `DB_*` vars) — set that
instead if your Postgres provider only gives you one URL rather than
separate fields.

**Free-tier tradeoff:** Render's free web service spins down after 15
minutes idle; the first request after that takes ~30-50s to wake up. Fine
for a demo or small class, not for something you need always-warm.

### Static files & production hardening
- `whitenoise` serves collected static files directly from the Django
  process — no S3/CDN needed for a free deploy.
- `SECURE_PROXY_SSL_HEADER` is set so Django correctly detects HTTPS behind
  Render's (or any) reverse proxy — needed for CSRF to work over HTTPS.
- Set `DJANGO_DEBUG=False` in production; `DEBUG` defaults to `True` for
  local dev only.
