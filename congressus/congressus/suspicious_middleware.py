from django.core.exceptions import SuspiciousOperation
from django.views.defaults import server_error


class SuspiciousMiddleware:
    ''' Avoid send error with InvalidHost '''

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self.process_request(request)
        return response

    def process_request(self, request):
        try:
            # throw SuspiciousOperation when host not in ALLOWED_HOSTS
            request.get_host()
        except SuspiciousOperation:
            return server_error(request)
