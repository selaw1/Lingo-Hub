import io

import pandas as pd
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from attendance.models import Attendance
from loyalty.models import Tier
from loyalty.utils import get_user_tier


@login_required
def wallet_view(request):
    tier, stamp_count = get_user_tier(request.user)
    next_tier = Tier.objects.filter(min_stamps__gt=stamp_count).order_by("min_stamps").first()
    tiers = Tier.objects.all()
    return render(
        request,
        "loyalty/wallet.html",
        {
            "tier": tier,
            "stamp_count": stamp_count,
            "next_tier": next_tier,
            "tiers": tiers,
        },
    )


@staff_member_required
def export_view(request):
    attendance = Attendance.objects.all()

    session_id = request.GET.get("session_id")
    filename = "attendance_export.xlsx"
    if session_id:
        attendance = attendance.filter(session_id=session_id)
        filename = f"attendance_export_session_{session_id}.xlsx"

    df = pd.DataFrame(attendance.values("user__username", "session__title", "timestamp"))
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
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response
