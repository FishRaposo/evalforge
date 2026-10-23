"""Local browser Origin boundary and bounded multipart request buffering."""

from __future__ import annotations

from collections.abc import Sequence

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class LocalMutationBoundary:
    """Origins are a browser boundary only; this local service does not claim auth."""

    def __init__(self, app: ASGIApp, allowed_origins: Sequence[str]) -> None:
        self.app = app
        self.allowed_origins = set(allowed_origins)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        mutation = (
            scope["type"] == "http"
            and scope.get("method") == "POST"
            and scope.get("path") in {"/api/evaluations", "/api/evaluation-profiles"}
        )
        if not mutation:
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers", []))
        origin = headers.get(b"origin")
        if origin is not None and origin.decode("latin-1") not in self.allowed_origins:
            await JSONResponse(
                {"detail": "Origin denied; configure EVALFORGE_ALLOWED_ORIGINS"},
                403,
            )(scope, receive, send)
            return
        if scope["path"] != "/api/evaluation-profiles":
            await self.app(scope, receive, send)
            return
        # Bound even chunked uploads before the multipart parser spools any files.
        limit = 13 * 1024 * 1024
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > limit:
                await JSONResponse(
                    {"detail": "Multipart upload exceeds 13 MiB request limit"}, 413
                )(scope, receive, send)
                return
            if not message.get("more_body", False):
                break
        delivered = False

        async def replay() -> Message:
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)
