from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.signing import BadSignature, SignatureExpired
from django.shortcuts import get_object_or_404, redirect, render
from django_ratelimit.decorators import ratelimit

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
    attendance, created = Attendance.objects.get_or_create(user=request.user, session=session)
    if created:
        # guard matters — without it, a blocked duplicate scan (caught by
        # unique_together) would still try to award a second stamp
        Stamp.objects.create(user=request.user, source="attendance", attendance=attendance)

    return redirect("wallet")


@staff_member_required
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
