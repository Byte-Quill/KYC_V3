from django.core.cache import cache
from rest_framework.throttling import AnonRateThrottle, BaseThrottle


class LoginThrottle(BaseThrottle):
    """Per-credential login throttle (email + IP) to stop stuffing one account.

    Keying on email alone would let an attacker distribute attempts across
    many accounts; keying on IP alone would poison a shared proxy/NAT address
    for everyone behind it. Using both bounds both attacks.
    """

    def allow_request(self, request, view):
        ident = self.get_ident(request)
        email = (request.data.get("email") or "").strip().lower()
        key = f"login-throttle:{email}:{ident}"
        count = cache.get(key, 0)
        if count >= 10:
            return False
        cache.set(key, count + 1, 60 * 10)
        return True


class RegisterThrottle(AnonRateThrottle):
    rate = "5/hour"
