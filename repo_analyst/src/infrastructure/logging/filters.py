"""
Logging filters for structured logging.
"""
import logging
from threading import local

_thread_locals = local()


def set_request_id(request_id):
    """Set request ID for current thread."""
    _thread_locals.request_id = request_id


def get_request_id():
    """Get request ID for current thread."""
    return getattr(_thread_locals, "request_id", "no-request-id")


class RequestIDFilter(logging.Filter):
    """Filter to add request_id to log records."""

    def filter(self, record):
        record.request_id = get_request_id()
        return True
