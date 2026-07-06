from loyalty.models import Stamp, Tier


def get_user_tier(user):
    stamp_count = Stamp.objects.filter(user=user).count()
    tier = Tier.objects.filter(min_stamps__lte=stamp_count).order_by("-min_stamps").first()
    return tier, stamp_count
