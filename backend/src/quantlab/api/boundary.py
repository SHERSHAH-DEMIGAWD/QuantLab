"""Bound bodies before JSON parsing; reject nonlocal Hosts and ambiguous JSON."""

from urllib.parse import urlsplit

from starlette.responses import JSONResponse

from quantlab.application.requests import MAX_CONFIGURATION_BYTES
from quantlab.persistence.codec import loads

MAX_IMPORT_REQUEST_BYTES = 12 * 1024 * 1024
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


def error_response(status: int, code: str, message: str, details=None) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message, "details": details}}, status_code=status)


class LocalBoundary:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", ()))
        try:
            host = urlsplit("http://" + headers.get(b"host", b"").decode("ascii"))
            if host.hostname not in LOOPBACK_HOSTS or host.username or host.password or host.path or host.query or host.fragment:
                raise ValueError
            host.port  # Validate the optional port too.
        except (ValueError, UnicodeError):
            return await error_response(400, "invalid_host", "A loopback Host is required.")(scope, receive, send)
        if scope["method"] in ("POST", "PUT", "PATCH") and b"origin" in headers:
            try:
                origin = urlsplit(headers[b"origin"].decode("ascii"))
                if origin.hostname not in LOOPBACK_HOSTS or origin.scheme not in ("http", "https"):
                    raise ValueError
            except (ValueError, UnicodeError):
                return await error_response(403, "invalid_origin", "A nonlocal request origin is not accepted.")(scope, receive, send)
        limit = MAX_IMPORT_REQUEST_BYTES if scope["path"] == "/api/v1/datasets" and scope["method"] == "POST" else MAX_CONFIGURATION_BYTES
        try:
            length = int(headers.get(b"content-length", b"0"))
            if length < 0:
                raise ValueError
        except ValueError:
            return await error_response(400, "invalid_length", "Invalid Content-Length.")(scope, receive, send)
        if length > limit:
            return await error_response(413, "request_too_large", "Request body exceeds the route's byte limit.")(scope, receive, send)
        if headers.get(b"content-encoding", b"identity").lower() != b"identity":
            return await error_response(415, "unsupported_encoding", "Compressed request bodies are not supported.")(scope, receive, send)
        chunks, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > limit:
                return await error_response(413, "request_too_large", "Request body exceeds the route's byte limit.")(scope, receive, send)
            chunks.append(chunk)
            if not message.get("more_body", False):
                break
        body = b"".join(chunks)
        if scope["path"].endswith("/reproduce") and body:
            return await error_response(422, "invalid_request", "Reproduction accepts no body; it uses the saved request.")(scope, receive, send)
        if body:
            if headers.get(b"content-type", b"").split(b";")[0].strip().lower() != b"application/json":
                return await error_response(415, "unsupported_media_type", "Use application/json.")(scope, receive, send)
            try:
                loads(body.decode("utf-8"))
            except (ValueError, UnicodeError, RecursionError):
                return await error_response(400, "invalid_json", "Use UTF-8 standard JSON with unique object keys.")(scope, receive, send)
        delivered = False
        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()
        return await self.app(scope, replay, send)
