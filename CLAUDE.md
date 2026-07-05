# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Lingo Hub** is a Django QR attendance + loyalty system for teachers and students:
- Teachers create sessions and display QR codes for students to scan
- Students scan QR codes to record attendance and earn loyalty stamps
- Stamps accumulate toward tiers (Bronze/Silver/Gold/etc)
- Students can view their stamp count, current tier, and progress on a wallet page
- Admin users can export attendance records to Excel and view session attendees

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

### Session Attendees View (admin only)
- Restricted to `@staff_member_required` (admin users only)
- **Not** based on session ownership — only `is_staff` matters
- Teachers that need this view must have `is_staff=True` set via Django admin
- Path: `/attendance/sessions/<session_id>/attendees/`

### Wallet Page (loyalty/views.py)
- Shows total stamps and current tier
- Shows next tier and progress (e.g. "7/10 stamps to Gold")
- Optional: tier ladder with current tier highlighted
- Uses `get_user_tier()` helper to derive current state

### Excel Export
```python
import pandas as pd
from attendance.models import Attendance

def export_attendance():
    df = pd.DataFrame(Attendance.objects.all().values(
        "user__username", "session__title", "timestamp"
    ))
    return df.to_excel("attendance_export.xlsx", index=False)
```
Can add per-session export on the session attendees page by filtering `Attendance.objects.filter(session=session_id)`.

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
7. **Session attendees view is `@staff_member_required`** — admin/staff only, not ownership-based
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
