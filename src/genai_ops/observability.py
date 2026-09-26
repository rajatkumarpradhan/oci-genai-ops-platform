"""Metrics and structured logging for pipeline runs.

Mirrors OCI Monitoring / Logging shapes: counters, latency histograms,
and JSON-structured log events with a trace id per request.
"""
from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field


class MetricsRegistry:
    def __init__(self, namespace: str = "genai_ops") -> None:
        self.namespace = namespace
        self._counters: dict[str, float] = {}
        self._timers: dict[str, list[float]] = {}

    def increment(self, name: str, value: float = 1.0, **tags: str) -> None:
        key = self._key(name, tags)
        self._counters[key] = self._counters.get(key, 0.0) + value

    def observe_ms(self, name: str, value_ms: float, **tags: str) -> None:
        key = self._key(name, tags)
        self._timers.setdefault(key, []).append(value_ms)

    def _key(self, name: str, tags: dict) -> str:
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"

    @contextmanager
    def timed(self, name: str, **tags: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            self.observe_ms(name, (time.perf_counter() - start) * 1000.0, **tags)

    def snapshot(self) -> dict:
        timers = {}
        for key, values in self._timers.items():
            ordered = sorted(values)
            n = len(ordered)
            timers[key] = {
                "count": n,
                "p50_ms": round(ordered[n // 2], 3),
                "p95_ms": round(ordered[min(int(n * 0.95), n - 1)], 3),
                "max_ms": round(ordered[-1], 3),
            }
        return {"namespace": self.namespace, "counters": dict(self._counters), "timers": timers}


@dataclass
class Trace:
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    spans: list = field(default_factory=list)

    @contextmanager
    def span(self, name: str, **attrs: str):
        start = time.perf_counter()
        error = None
        try:
            yield
        except Exception as exc:  # re-raised after recording
            error = type(exc).__name__
            raise
        finally:
            self.spans.append({
                "name": name,
                "duration_ms": round((time.perf_counter() - start) * 1000.0, 3),
                "error": error,
                "attrs": attrs,
            })

    def to_dict(self) -> dict:
        return {"trace_id": self.trace_id, "spans": self.spans}


class StructuredLogger:
    def __init__(self, level: str = "INFO") -> None:
        self.level = level
        self.events: list[dict] = []

    def log(self, severity: str, message: str, **fields) -> dict:
        event = {
            "ts": round(time.time(), 3),
            "severity": severity,
            "message": message,
            **fields,
        }
        self.events.append(event)
        return event

    def info(self, message: str, **fields) -> dict:
        return self.log("INFO", message, **fields)

    def warning(self, message: str, **fields) -> dict:
        return self.log("WARNING", message, **fields)

    def error(self, message: str, **fields) -> dict:
        return self.log("ERROR", message, **fields)

    def as_json_lines(self) -> str:
        return "\n".join(json.dumps(e, sort_keys=True) for e in self.events)
