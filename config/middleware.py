import traceback

from django.conf import settings
from django.http import JsonResponse


class JsonApiExceptionMiddleware:
    """
    Ensure API endpoints return JSON on unexpected server errors.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as exc:
            if request.path.startswith('/api/'):
                payload = {
                    'detail': 'Internal server error',
                    'error': exc.__class__.__name__,
                }
                if settings.DEBUG:
                    payload['message'] = str(exc)
                    payload['traceback'] = traceback.format_exc()
                return JsonResponse(payload, status=500)
            raise
