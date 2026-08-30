"""A ceiling on what one process will spend against the OpenAI account.

The demo runs on a personal key with no spend limit set at the provider, and
the chat route is reachable by anyone who can reach the API. A loop in the
frontend, a stuck retry, or someone holding down enter is enough to run up a
bill that nobody notices until the invoice.

The cap counts calls and tokens rather than currency on purpose. Pricing for
the chat model is not something this code can look up, so a dollar figure here
would be a guess presented as a measurement.

Counters are per process and reset on restart. That is the right scope for a
demo backend and the wrong scope for anything multi-instance, which would need
the count in shared storage.
"""
from __future__ import annotations

import os
import threading
from dataclasses import dataclass

DEFAULT_MAX_CALLS = 500
DEFAULT_MAX_TOKENS = 2_000_000


class BudgetExceeded(RuntimeError):
    """Raised instead of making a call that would cross the ceiling."""


@dataclass
class Usage:
    calls: int = 0
    tokens: int = 0


class Budget:
    def __init__(self, max_calls: int | None = None, max_tokens: int | None = None):
        self.max_calls = max_calls if max_calls is not None else _env_int(
            "CANOPYCAST_MAX_CALLS", DEFAULT_MAX_CALLS
        )
        self.max_tokens = max_tokens if max_tokens is not None else _env_int(
            "CANOPYCAST_MAX_TOKENS", DEFAULT_MAX_TOKENS
        )
        self._usage = Usage()
        # Uvicorn serves requests from a thread pool, so two chat requests can
        # land in check() at the same moment and both pass a ceiling that only
        # one of them should.
        self._lock = threading.Lock()

    def check(self) -> None:
        with self._lock:
            if self.max_calls and self._usage.calls >= self.max_calls:
                raise BudgetExceeded(
                    f"call budget spent: {self._usage.calls} of {self.max_calls} "
                    "OpenAI calls used since this process started. Raise "
                    "CANOPYCAST_MAX_CALLS or restart."
                )
            if self.max_tokens and self._usage.tokens >= self.max_tokens:
                raise BudgetExceeded(
                    f"token budget spent: {self._usage.tokens} of "
                    f"{self.max_tokens} tokens used since this process started. "
                    "Raise CANOPYCAST_MAX_TOKENS or restart."
                )

    def record(self, response) -> None:
        """Count one call, and its tokens when the response reports them.

        A response with no usage block still counts as a call. Skipping it
        would make an unparseable response the cheapest way past the ceiling.
        """
        tokens = 0
        usage = getattr(response, "usage", None)
        total = getattr(usage, "total_tokens", None)
        if isinstance(total, int):
            tokens = total
        with self._lock:
            self._usage.calls += 1
            self._usage.tokens += tokens

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "calls": self._usage.calls,
                "max_calls": self.max_calls,
                "tokens": self._usage.tokens,
                "max_tokens": self.max_tokens,
            }


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    # 0 disables the ceiling; a negative value is a typo, not a request for an
    # unlimited budget.
    return value if value >= 0 else default


BUDGET = Budget()
