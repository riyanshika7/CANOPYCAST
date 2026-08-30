"""Suite-wide isolation from the developer's environment.

app.config loads backend/.env on import, so once a real key sits in that file
every test that exercises a "no key configured" path silently takes the
"key present" branch instead. Worse, anything that slipped past a fake client
would bill the real account. The key is removed for every test; the handful of
tests that need one inject a stub client directly.
"""
import os

import pytest


@pytest.fixture(autouse=True)
def _no_real_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    yield
