"""
Middleware for adding request ID to all requests.
"""
import uuid


class RequestIDMiddleware:
    """Middleware to add a unique request ID to each request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.request_id = request_id

        # Add to response headers
        response = self.get_response(request)
        response["X-Request-ID"] = request_id

        return response
