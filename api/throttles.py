from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'


class UserApiRateThrottle(UserRateThrottle):
    scope = 'user'


class WriteRateThrottle(ScopedRateThrottle):
    scope = 'write'


class AutocompleteRateThrottle(ScopedRateThrottle):
    scope = 'autocomplete'
