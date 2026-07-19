"""Server-Sent Events broker for live crawl progress.

A module-level ``CrawlEventBroker`` singleton lets the scheduler / crawl
worker (running in a threadpool) publish progress events keyed by source
slug, while the FastAPI SSE generator (async) consumes them from an
``asyncio.Queue``. The special key ``"__all__"`` is used by the
crawl-all stream.

Architecture::

    Admin client ──POST /admin/sources/{slug}/crawl/stream──> FastAPI
      ├─ StreamingResponse(generator) drains asyncio.Queue
      └─ run_in_threadpool(job_crawl_source_streaming, slug, broker)
            └─ per page: broker.publish(slug, {"type":"progress",...})

The generator's ``finally`` always unsubscribes so disconnected clients
don't leak queues.
"""
from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Any


class CrawlEventBroker:
    """Module-level singleton broker.

    Each key (source slug or ``"__all__"``) has a list of ``asyncio.Queue``
    subscribers. ``publish`` is non-blocking (uses ``put_nowait``) so a
    worker thread can push events without awaiting.
    """

    def __init__(self) -> None:
        self._subs: dict[str, list[asyncio.Queue]] = defaultdict(list)
        # The loop is captured at subscribe time so put_nowait targets the
        # correct event loop even when publish is called from a worker thread.
        self._loop: asyncio.AbstractEventLoop | None = None

    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.get_event_loop()
        return self._loop

    def subscribe(self, key: str) -> asyncio.Queue:
        """Register a new subscriber for ``key`` and return its queue."""
        loop = self._ensure_loop()
        q: asyncio.Queue = asyncio.Queue(maxsize=256)
        self._subs[key].append(q)
        return q

    def unsubscribe(self, key: str, q: asyncio.Queue) -> None:
        """Remove a subscriber queue. Safe to call if not registered."""
        try:
            self._subs[key].remove(q)
        except ValueError:
            pass
        if not self._subs[key]:
            self._subs.pop(key, None)

    def publish(self, key: str, event: dict[str, Any]) -> None:
        """Push ``event`` to every subscriber of ``key``.

        Non-blocking: a full queue drops the event rather than blocking the
        worker thread. This is intentional — a slow SSE client should not
        stall the crawl.
        """
        for q in list(self._subs.get(key, [])):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # Drop overflow events; the client will still see the
                # terminal "done" event when it arrives.
                pass


def format_sse(event_type: str, data: Any) -> str:
    """Serialize an SSE frame: ``event: <type>\\ndata: <json>\\n\\n``."""
    payload = json.dumps(data, default=str, ensure_ascii=False)
    return f"event: {event_type}\ndata: {payload}\n\n"


# Module-level singleton
broker = CrawlEventBroker()