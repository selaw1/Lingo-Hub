from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import UserCreationForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect("wallet")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("wallet")
    else:
        form = UserCreationForm()

    return render(request, "accounts/register.html", {"form": form})
