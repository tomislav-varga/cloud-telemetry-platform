from __future__ import annotations

from contextvars import ContextVar, Token

_TRACE_ID: ContextVar[str | None] = ContextVar("trace_id", default=None)


def set_trace_id(trace_id: str) -> Token[str | None]:
    return _TRACE_ID.set(trace_id)


def get_trace_id() -> str | None:
    return _TRACE_ID.get()


def reset_trace_id(token: Token[str | None]) -> None:
    _TRACE_ID.reset(token)
