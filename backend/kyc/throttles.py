from django.core.cache import cache
from rest_framework.throttling import AnonRateThrottle, BaseThrottle, ScopedRateThrottle


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


class WriteThrottle(ScopedRateThrottle):
    """User-scoped throttle for state-changing endpoints (uploads, submit, review)."""

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            # Key per user, not per IP: NAT/proxy users should not be pooled.
            return f"write-throttle:{request.user.pk}:{self.scope}"
        # Anonymous fallback: throttle by IP to prevent unauthenticated DoS.
        ident = self.get_ident(request)
        return f"write-throttle:anon:{ident}:{self.scope}"
