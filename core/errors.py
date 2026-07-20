"""Client-safe error message sanitization.

Network and external-service failures must never leak raw payloads, URLs,
tool-call-shaped content, or internal tracebacks to the API client. Every
adapter / scheduler / SSE stream wraps its external calls in try/except and
converts the caught exception via ``sanitize_error`` before exposing it.

Mapping (ordered — first match wins):
  requests.ConnectionError | requests.Timeout  -> "Échec réseau"
  httpx.HTTPError                              -> "Erreur HTTP source"
  openai.* | key errors | TimeoutError          -> "Erreur du service IA"
  generic Exception                            -> "Erreur inattendue"

The original exception should still be logged server-side via
``logger.exception`` — only the returned string is sanitized.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def sanitize_error(exc: BaseException) -> str:
    """Return a generic French error string safe for client display.

    Never includes the raw message, URL, request payload, or tool-call-shaped
    content. The original exception is logged at debug level for server-side
    diagnosis.
    """
    # Lazy imports so the module is importable even if a lib is missing.
    try:
        import requests as _requests
        if isinstance(exc, (_requests.ConnectionError, _requests.Timeout)):
            logger.debug("sanitized network error: %r", exc)
            return "Échec réseau"
    except Exception:  # pragma: no cover — requests always installed
        pass

    try:
        import httpx as _httpx
        if isinstance(exc, _httpx.HTTPError):
            logger.debug("sanitized httpx error: %r", exc)
            return "Erreur HTTP source"
    except Exception:
        pass

    # AI service errors: openai, qwen, key errors, timeouts.
    try:
        import openai as _openai
        if isinstance(exc, _openai.APIError):
            return "Erreur du service IA"
    except Exception:
        pass
    if isinstance(exc, TimeoutError):
        return "Erreur du service IA"
    # Key errors raised when a Qwen/OpenAI key is missing/invalid.
    if isinstance(exc, (KeyError, PermissionError)):
        return "Erreur du service IA"

    logger.debug("sanitized generic error: %r", exc)
    return "Erreur inattendue"