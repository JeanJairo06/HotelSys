from hashlib import sha256

from django.conf import settings
from django.core.cache import cache


class LoginAttemptRateLimiter:
    def __init__(self, request):
        self.request = request
        username = request.POST.get('username', '').strip().casefold()
        ip_address = request.META.get('REMOTE_ADDR', '')
        self.keys = (
            self._cache_key('ip', ip_address),
            self._cache_key('username', username),
        )

    @staticmethod
    def _cache_key(category, value):
        digest = sha256(f'{category}:{value}'.encode()).hexdigest()
        return f'login-attempt:{category}:{digest}'

    def allow_attempt(self):
        maximum_attempts = settings.LOGIN_RATE_LIMIT_ATTEMPTS
        if any(cache.get(key, 0) >= maximum_attempts for key in self.keys):
            return False

        return all(self._increment(key) <= maximum_attempts for key in self.keys)

    def reset(self):
        cache.delete_many(self.keys)

    @staticmethod
    def _increment(key):
        cache.add(key, 0, timeout=settings.LOGIN_RATE_LIMIT_WINDOW)
        return cache.incr(key)
