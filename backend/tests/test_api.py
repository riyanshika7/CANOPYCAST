"""HTTP-layer tests for the CanopyCast FastAPI app.

The other suites cover each module in isolation. These tests pin down the
wiring: that routes return the documented status codes and response shapes,
that the lifespan hook seeds the grid, and that the documented degraded
behaviour holds when no corpus and no API key are present.
"""
import json
import math
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import config, main
from app.schema import Cell, GRID_SIZE


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def real_db_path() -> Path:
    """The developer's default DB location.

    Tests must never create OR modify this file. Asserting it is simply absent
    fails on any machine where the app has been run once, which is every
    developer machine, so the check compares before against after instead.
    """
    return Path(config.__file__).resolve().parent.parent / "canopycast.db"


@pytest.fixture
def client(tmp_path: Path, real_db_path: Path, monkeypatch):
    """A TestClient whose app writes to a tmp DB and tmp chroma dir.

    Pointing `app.config.DB_PATH` at a tmp file means the lifespan hook seeds
    there instead of at the real backend/canopycast.db. `app.config.CHROMA_DIR`
    is pointed at a tmp directory so the chat route sees no corpus and takes
    the documented degraded path.
    """
    tmp_db = tmp_path / "canopycast.db"
    tmp_chroma = tmp_path / "chroma_db"
    monkeypatch.setattr(main.config, "DB_PATH", str(tmp_db))
    monkeypatch.setattr(main.config, "CHROMA_DIR", str(tmp_chroma))
    # The RAG retriever caches on a module-level dict in main. Clear any state
    # left by another test so the first chat call is the one that fails.
    main._rag_state.clear()
    before = (
        real_db_path.stat().st_mtime_ns if real_db_path.exists() else None
    )

    with TestClient(main.app) as c:
        yield c

    # The lifespan hook seeds a grid. It must have gone to the tmp path, so the
    # developer's own database is neither created nor touched.
    after = real_db_path.stat().st_mtime_ns if real_db_path.exists() else None
    assert after == before, "the test suite wrote to the real canopycast.db"
    assert tmp_db.exists(), "the app did not seed into the tmp database"


# ---------------------------------------------------------------------------
# 1. Root route
# ---------------------------------------------------------------------------


def test_root_names_the_service(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "CanopyCast API"
    assert "docs" in body


# ---------------------------------------------------------------------------
# 2. Health
# ---------------------------------------------------------------------------


def test_health_after_startup(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    # Lifespan seeded the DB into tmp_path, so grid_ready must be true.
    assert body["grid_ready"] is True
    # chroma dir was tmp and never populated, so chat is degraded.
    assert body["corpus_ready"] is False
    assert body["chat_ready"] is False
    # chat_model is the configured string, not a bool.
    assert isinstance(body["chat_model"], str)
    assert body["chat_model"] == config.CHAT_MODEL


# ---------------------------------------------------------------------------
# 3. City grid
# ---------------------------------------------------------------------------


def test_city_grid_returns_400_validating_cells(client: TestClient) -> None:
    response = client.get("/api/city-grid")
    assert response.status_code == 200
    body = response.json()
    assert body["city"] == "Kolkata"
    assert body["grid_size"] == GRID_SIZE
    cells = body["cells"]
    assert len(cells) == GRID_SIZE * GRID_SIZE
    # Every entry must validate against Cell. A 400-length list of dicts that
    # happens to round-trip through json.dumps is not the same thing.
    parsed = [Cell.model_validate(c) for c in cells]
    assert len(parsed) == 400

    temps = [c.base_temperature for c in parsed]
    mean = body["city_mean_temperature"]
    # The reported mean must sit between the observed min and max cell temps.
    assert min(temps) <= mean <= max(temps)
    # And the mean must agree with the per-cell mean to a tight tolerance, so a
    # bug that stored the global max as the mean is caught.
    expected_mean = sum(temps) / len(temps)
    assert mean == pytest.approx(expected_mean, rel=1e-6)


# ---------------------------------------------------------------------------
# 4. Unknown city is 404, not 200, not 500
# ---------------------------------------------------------------------------


def test_city_grid_unknown_city_returns_404_not_500(client: TestClient) -> None:
    response = client.get("/api/city-grid", params={"city": "Atlantis"})
    assert response.status_code == 404
    # Not a 500 and not an empty 200: the body must describe the problem so the
    # frontend can show a useful error.
    detail = response.json()["detail"]
    assert "Atlantis" in detail


# ---------------------------------------------------------------------------
# 5. Cell stats: inside the grid
# ---------------------------------------------------------------------------


def test_cell_stats_inside_grid_returns_containing_cell(client: TestClient) -> None:
    grid = client.get("/api/city-grid").json()
    sample = grid["cells"][len(grid["cells"]) // 2]
    response = client.get(
        "/api/cell-stats",
        params={"lat": sample["lat"], "lon": sample["lon"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["cell_id"] == sample["cell_id"]
    # Returned coords must lie within one cell of the queried point. If they
    # don't, the snap routine has regressed and is handing back the wrong cell.
    assert math.hypot(body["lat"] - sample["lat"], body["lon"] - sample["lon"]) <= 0.005
    # Same density comes back as a known string, not something the DB made up.
    assert body["population_density"] in {"Low", "Medium", "High"}


# ---------------------------------------------------------------------------
# 6. Cell stats: London must NOT clamp to a Kolkata corner cell
# ---------------------------------------------------------------------------


def test_cell_stats_london_returns_404_not_clamp(client: TestClient) -> None:
    response = client.get(
        "/api/cell-stats",
        params={"lat": 51.5074, "lon": -0.1278},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 7. Cell stats: unknown city is 404, not 500
# ---------------------------------------------------------------------------


def test_cell_stats_unknown_city_returns_404_not_500(client: TestClient) -> None:
    response = client.get(
        "/api/cell-stats",
        params={"city": "Atlantis", "lat": 22.57, "lon": 88.36},
    )
    assert response.status_code == 404
    assert "Atlantis" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 8. Cell stats: bad input is 422
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("missing", ["lat", "lon"])
def test_cell_stats_missing_coord_returns_422(
    client: TestClient, missing: str
) -> None:
    params = {"lat": 22.57, "lon": 88.36}
    params.pop(missing)
    response = client.get("/api/cell-stats", params=params)
    assert response.status_code == 422


def test_cell_stats_non_numeric_coord_returns_422(client: TestClient) -> None:
    response = client.get("/api/cell-stats", params={"lat": "not-a-number", "lon": 88.36})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 9. Optimize: happy path
# ---------------------------------------------------------------------------


def test_optimize_top_n_sites_sorted_and_explained(client: TestClient) -> None:
    response = client.post("/api/optimize", json={"city": "Kolkata", "top_n": 5})
    assert response.status_code == 200
    body = response.json()
    assert body["city"] == "Kolkata"
    sites = body["sites"]
    assert len(sites) == 5
    scores = [s["priority_score"] for s in sites]
    # Descending order matters for the dashboard's "top ranked" feel.
    assert scores == sorted(scores, reverse=True)
    for site in sites:
        breakdown = site["score_breakdown"]
        # The reported score is the sum of its parts, not a recomputation.
        assert math.isclose(
            sum(breakdown.values()), site["priority_score"], rel_tol=1e-4, abs_tol=1e-4
        )
        assert len(breakdown) >= 1
        # Rationale has to read like a sentence, not be empty.
        assert isinstance(site["rationale"], str)
        assert site["rationale"].strip()


# ---------------------------------------------------------------------------
# 9. Optimize: out-of-bounds top_n is 422 from schema validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("top_n", [0, -1, 26])
def test_optimize_bad_top_n_returns_422(client: TestClient, top_n: int) -> None:
    response = client.post(
        "/api/optimize", json={"city": "Kolkata", "top_n": top_n}
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 10. Optimize: unknown city is 404
# ---------------------------------------------------------------------------


def test_optimize_unknown_city_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/optimize", json={"city": "Atlantis", "top_n": 5}
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 11. Chat: no corpus, no API key => 503 with a readable detail, no 500, no traceback
# ---------------------------------------------------------------------------


def test_chat_without_corpus_returns_503_with_readable_detail(
    client: TestClient,
) -> None:
    payload = {"message": "What should I plant here?", "session_id": "s1"}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert isinstance(detail, str) and detail
    # A leaked Python traceback would be wrapped in a traceback module path.
    assert "Traceback" not in detail
    assert "File \"" not in detail


# ---------------------------------------------------------------------------
# 12. Determinism: identical payloads back-to-back
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", ["/", "/api/health", "/api/city-grid"])
def test_two_calls_same_endpoint_identical(client: TestClient, path: str) -> None:
    a = client.get(path)
    b = client.get(path)
    assert a.status_code == b.status_code == 200
    assert a.json() == b.json()


def test_two_optimize_calls_identical(client: TestClient) -> None:
    a = client.post("/api/optimize", json={"city": "Kolkata", "top_n": 5})
    b = client.post("/api/optimize", json={"city": "Kolkata", "top_n": 5})
    assert a.status_code == b.status_code == 200
    assert a.json() == b.json()


# ---------------------------------------------------------------------------
# 13. CORS preflight is permitted
# ---------------------------------------------------------------------------


def test_cors_preflight_allowed_from_browser_origin(client: TestClient) -> None:
    response = client.options(
        "/api/city-grid",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    # 200 is what starlette sends when allow_origins=["*"] matches a wildcard.
    assert response.status_code in (200, 204)
    allow_origin = response.headers.get("access-control-allow-origin")
    assert allow_origin in {"*", "http://localhost:5173"}
    # The preflight asked specifically for GET; that method must be echoed back.
    assert "GET" in response.headers.get("access-control-allow-methods", "")


# ---------------------------------------------------------------------------
# recommend-trees
# ---------------------------------------------------------------------------


def test_recommend_trees_degrades_without_a_key(client):
    """Same degraded contract as chat: 503, readable, no traceback."""
    r = client.get("/api/recommend-trees", params={"city": "Kolkata"})
    assert r.status_code == 503
    detail = r.json()["detail"]
    assert "OPENAI_API_KEY" in detail
    assert "Traceback" not in detail


def test_recommend_trees_validates_n(client):
    for bad in (0, -1, 9, 100):
        r = client.get("/api/recommend-trees", params={"n": bad})
        assert r.status_code == 422, f"n={bad} should be rejected"
    # a value inside the range gets past validation and fails later on the key
    assert client.get("/api/recommend-trees", params={"n": 3}).status_code == 503


def test_every_sprint_endpoint_is_mounted():
    """The sprint plan names six routes. A missing one is a silent scope gap."""
    paths = {r.path for r in main.app.routes if hasattr(r, "path")}
    for expected in (
        "/api/health",
        "/api/city-grid",
        "/api/cell-stats",
        "/api/optimize",
        "/api/chat",
        "/api/recommend-trees",
    ):
        assert expected in paths, f"{expected} is not mounted"


# ---------------------------------------------------------------------------
# Chat: the frontend's minimal payload must not 422
# ---------------------------------------------------------------------------


def test_chat_without_session_id_is_accepted(client: TestClient) -> None:
    """Chatbot.jsx posts {message} alone and falls back to canned text on any
    error, so a 422 here shows the user invented advice with no citations."""
    response = client.post("/api/chat", json={"message": "which trees should I plant"})
    assert response.status_code != 422, response.text


def test_chat_anonymous_sessions_do_not_share_history(client: TestClient) -> None:
    from app.schema import ChatRequest

    first = ChatRequest(message="a").session_id
    second = ChatRequest(message="b").session_id
    assert first != second


# ---------------------------------------------------------------------------
# Budget ceiling
# ---------------------------------------------------------------------------


def test_health_reports_usage_against_the_ceiling(client: TestClient) -> None:
    usage = client.get("/api/health").json()["usage"]
    assert {"calls", "max_calls", "tokens", "max_tokens"} <= set(usage)


def test_chat_over_budget_is_429_not_502(client: TestClient, monkeypatch) -> None:
    """A spent budget is this process's own limit, not an upstream fault."""
    from app import main as main_module
    from app.budget import BudgetExceeded

    def _spent(*args, **kwargs):
        raise BudgetExceeded("call budget spent: 500 of 500")

    monkeypatch.setattr(main_module, "_get_rag", lambda: (object(), object()))
    import app.rag as rag_module

    monkeypatch.setattr(rag_module, "answer", _spent)
    response = client.post("/api/chat", json={"message": "hi"})
    assert response.status_code == 429
    assert "budget" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Streaming chat
# ---------------------------------------------------------------------------


def _sse_events(response):
    out = []
    for line in response.text.splitlines():
        if line.startswith("data: "):
            out.append(json.loads(line[6:]))
    return out


def test_chat_stream_emits_tokens_then_citations_then_done(client, monkeypatch):
    from app import main as main_module
    import app.rag as rag_module
    from app.schema import Citation

    def fake_stream(req, retriever, store, client=None):
        yield "token", "Plant "
        yield "token", "Neem."
        yield "citations", [Citation(doc_title="Avenue Trees for Kolkata", page=3, snippet="x")]

    monkeypatch.setattr(main_module, "_get_rag", lambda: (object(), object()))
    monkeypatch.setattr(rag_module, "answer_stream", fake_stream)

    response = client.post("/api/chat/stream", json={"message": "hi"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    events = _sse_events(response)
    assert "".join(e["token"] for e in events if "token" in e) == "Plant Neem."
    assert events[-1] == {"done": True}
    citations = [e for e in events if "citations" in e]
    assert len(citations) == 1
    assert citations[0]["citations"][0]["doc_title"] == "Avenue Trees for Kolkata"


def test_chat_stream_reports_a_late_failure_in_band(client, monkeypatch):
    """The 200 is already sent once the first token goes out, so a failure
    after that cannot be a status code."""
    from app import main as main_module
    import app.rag as rag_module

    def fake_stream(req, retriever, store, client=None):
        yield "token", "Plant "
        raise RuntimeError("upstream died")

    monkeypatch.setattr(main_module, "_get_rag", lambda: (object(), object()))
    monkeypatch.setattr(rag_module, "answer_stream", fake_stream)

    events = _sse_events(client.post("/api/chat/stream", json={"message": "hi"}))
    assert events[0] == {"token": "Plant "}
    assert "upstream died" in events[-1]["error"]
    assert not any("done" in e for e in events)
