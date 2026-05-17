from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler


ERROR_CODES = {
    status.HTTP_400_BAD_REQUEST: 'VALIDATION_ERROR',
    status.HTTP_401_UNAUTHORIZED: 'AUTHENTICATION_FAILED',
    status.HTTP_403_FORBIDDEN: 'PERMISSION_DENIED',
    status.HTTP_404_NOT_FOUND: 'NOT_FOUND',
    status.HTTP_405_METHOD_NOT_ALLOWED: 'METHOD_NOT_ALLOWED',
    status.HTTP_429_TOO_MANY_REQUESTS: 'THROTTLED',
    status.HTTP_500_INTERNAL_SERVER_ERROR: 'SERVER_ERROR',
}


def standard_exception_handler(exc, context):
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    response = exception_handler(exc, context)
    if response is None:
        return None

    message = 'No se pudo completar la solicitud.'
    if isinstance(response.data, dict) and response.data.get('detail'):
        message = str(response.data['detail'])

    response.data = {
        'error': True,
        'code': ERROR_CODES.get(response.status_code, 'API_ERROR'),
        'message': message,
        'detail': response.data,
    }
    return response
