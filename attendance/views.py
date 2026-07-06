import io

import pandas as pd
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.signing import BadSignature, SignatureExpired
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django_ratelimit.decorators import ratelimit

from common.decorators import host_or_admin_required
from loyalty.models import Stamp
from sessions.models import Session
from sessions.signing import signer

from .models import Attendance


@login_required
def scan_page_view(request):
    return render(request, "attendance/scan.html")


@login_required
def scan_error_view(request):
    return render(request, "attendance/scan_error.html")


@login_required
@ratelimit(key="user", rate="10/m", method="POST", block=False)
def scan_view(request):
    if getattr(request, "limited", False):
        messages.error(request, "Too many scan attempts. Please wait a moment and try again.")
        return redirect("scan_error")

    qr = request.POST.get("qr", "")
    try:
        session_id = signer.unsign(qr, max_age=180)
    except (BadSignature, SignatureExpired):
        # invalid or expired QR — show an error, do not create attendance
        messages.error(
            request, "This QR code is invalid or has expired. Ask your teacher for a fresh one."
        )
        return redirect("scan_error")

    session = get_object_or_404(Session, id=session_id, is_active=True)

    # Students may only be in one active session at a time. Re-scanning the
    # same session is allowed (and de-duplicated below).
    if not request.user.is_host_or_admin:
        in_other_active_session = (
            Attendance.objects.filter(user=request.user, session__is_active=True)
            .exclude(session=session)
            .exists()
        )
        if in_other_active_session:
            messages.error(
                request,
                "You're already checked in to an active session. "
                "You can join another one once it ends.",
            )
            return redirect("scan_error")

    attendance, created = Attendance.objects.get_or_create(user=request.user, session=session)
    if created:
        # guard matters — without it, a blocked duplicate scan (caught by
        # unique_together) would still try to award a second stamp
        Stamp.objects.create(user=request.user, source="attendance", attendance=attendance)

    return redirect("wallet")


@host_or_admin_required
def session_attendees_view(request, session_id):
    session = get_object_or_404(Session, id=session_id)

    attendees = (
        Attendance.objects.filter(session=session).select_related("user").order_by("timestamp")
    )

    return render(
        request,
        "attendance/session_attendees.html",
        {
            "session": session,
            "attendees": attendees,
            "count": attendees.count(),
        },
    )


@host_or_admin_required
def session_export_view(request, session_id):
    """Excel export of one session's attendance. Export only exists inside a
    session — there is deliberately no global export endpoint."""
    session = get_object_or_404(Session, id=session_id)

    df = pd.DataFrame(
        Attendance.objects.filter(session=session).values(
            "user__username", "session__title", "timestamp"
        )
    )
    if not df.empty:
        # Excel has no concept of timezone-aware datetimes; USE_TZ=True means
        # `timestamp` comes back UTC-aware, so drop the tzinfo before writing.
        df["timestamp"] = df["timestamp"].dt.tz_localize(None)

    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f"attachment; filename=attendance_{session_id}.xlsx"
    return response
