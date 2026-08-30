"""Tests for the OpenAI spend ceiling."""
import threading

import pytest

from app.budget import Budget, BudgetExceeded, _env_int


class _Resp:
    def __init__(self, total):
        self.usage = type("U", (), {"total_tokens": total})()


def test_calls_are_capped():
    b = Budget(max_calls=2, max_tokens=0)
    for _ in range(2):
        b.check()
        b.record(_Resp(5))
    with pytest.raises(BudgetExceeded, match="call budget"):
        b.check()


def test_tokens_are_capped():
    b = Budget(max_calls=0, max_tokens=10)
    b.check()
    b.record(_Resp(11))
    with pytest.raises(BudgetExceeded, match="token budget"):
        b.check()


def test_a_response_with_no_usage_still_counts_as_a_call():
    # Otherwise an unparseable response is the cheapest way past the ceiling.
    b = Budget(max_calls=1, max_tokens=0)
    b.record(object())
    with pytest.raises(BudgetExceeded):
        b.check()


def test_zero_disables_a_ceiling():
    b = Budget(max_calls=0, max_tokens=0)
    for _ in range(50):
        b.record(_Resp(10_000))
    b.check()


def test_concurrent_records_do_not_lose_counts():
    # Uvicorn serves from a thread pool, so record() races with itself.
    b = Budget(max_calls=0, max_tokens=0)
    threads = [threading.Thread(target=lambda: [b.record(_Resp(1)) for _ in range(200)])
               for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert b.snapshot()["calls"] == 1600
    assert b.snapshot()["tokens"] == 1600


def test_env_int_rejects_junk_and_negatives(monkeypatch):
    monkeypatch.setenv("X", "not a number")
    assert _env_int("X", 7) == 7
    monkeypatch.setenv("X", "-5")
    assert _env_int("X", 7) == 7
    monkeypatch.setenv("X", "0")
    assert _env_int("X", 7) == 0
