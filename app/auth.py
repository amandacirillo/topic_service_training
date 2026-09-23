"""Simple shared-secret API key auth for /api/* endpoints."""
from functools import wraps

from flask import request, jsonify

from app.settings import settings


def require_api_key(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        provided = request.headers.get('X-API-KEY') or _bearer_token(request.headers.get('Authorization'))
        if provided != settings.api_key:
            return jsonify({'error': 'Unauthorized'}), 401
        return view_func(*args, **kwargs)
    return wrapper


def _bearer_token(auth_header):
    if not auth_header:
        return None
    parts = auth_header.split(' ', 1)
    if len(parts) == 2 and parts[0].lower() in ('bearer', 'token'):
        return parts[1]
    return auth_header
