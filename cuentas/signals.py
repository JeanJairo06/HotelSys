from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from cuentas.session_state import initialize_session


@receiver(user_logged_in)
def initialize_user_session(sender, request, user, **kwargs):
    initialize_session(request)
