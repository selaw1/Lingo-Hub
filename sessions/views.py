import io

import qrcode
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Session
from .signing import generate_qr


@staff_member_required
def session_list_view(request):
    sessions = Session.objects.all()
    return render(request, "sessions/session_list.html", {"sessions": sessions})


@staff_member_required
def session_create_view(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        if title:
            session = Session.objects.create(title=title, created_by=request.user)
            return redirect("session_qr", session_id=session.id)
    return render(request, "sessions/session_create.html")


@staff_member_required
def session_qr_view(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    return render(request, "sessions/session_qr.html", {"session": session})


@staff_member_required
def session_qr_image_view(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    token = generate_qr(str(session.id))

    img = qrcode.make(token)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")

    response = HttpResponse(buffer.getvalue(), content_type="image/png")
    response["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response
