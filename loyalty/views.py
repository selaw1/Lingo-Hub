from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from loyalty.models import Tier
from loyalty.utils import get_user_tier


@login_required
def wallet_view(request):
    """Home page — the Lingo Card plus navigable sections."""
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
