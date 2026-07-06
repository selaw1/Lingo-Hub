from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def host_or_admin_required(view_func):
    """Allow only admins (is_staff) and hosts (user_type == "host").

    Students hitting a protected view get a 403 rather than a redirect —
    these URLs are never linked in their UI, so a hard stop is correct.
    """

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if request.user.is_host_or_admin:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied

    return _wrapped
