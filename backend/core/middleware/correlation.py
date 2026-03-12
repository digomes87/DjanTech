import uuid


class CorrelationIDMiddleware:
    HEADER = "HTTP_X_CORRELATION_ID"
    RESPONSE_HEADER = "X-Correlation-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        correlation_id = request.META.get(self.HEADER, str(uuid.uuid4()))
        request.correlation_id = correlation_id
        response = self.get_response(request)
        response[self.RESPONSE_HEADER] = correlation_id
        return response
