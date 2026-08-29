"""CanopyCast API.

Routes are thin. The grid lives in database.py, the scoring in optimize.py,
and retrieval plus answering in rag.py.
"""
import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .schema import (
    Cell,
    ChatRequest,
    ChatResponse,
    CityGrid,
    OptimizeRequest,
    OptimizeResponse,
    RecommendResponse,
)

log = logging.getLogger("canopycast")

# The retriever loads a Chroma collection and builds a BM25 corpus, which is
# slow and needs an API key. Chat is the only route that wants it, so it is
# built on first use and a failure degrades that one route instead of the app.
_rag_state: dict = {}

# A failure is remembered only briefly. Caching it forever meant that running
# `python -m app.ingest` against a live server left chat returning 503 until
# someone restarted the process, which is exactly the moment you cannot afford
# a restart. Retrying every request instead would stall each one on a slow
# Chroma open, so the failure is held for a short window and then retried.
_RAG_RETRY_AFTER_S = 20.0


def _reset_rag_cache() -> None:
    """Drop the cached retriever so the next request rebuilds it."""
    _rag_state.clear()


def _get_rag():
    from . import rag

    # A missing key is a deployment problem, not an upstream failure. Letting it
    # surface from the OpenAI call gave a 502 with a bare "OPENAI_API_KEY is not
    # set", which reads as a server fault. Answer 503 with the fix instead.
    if not config.has_openai_key():
        raise HTTPException(
            status_code=503,
            detail=(
                "chat is unavailable: OPENAI_API_KEY is not configured. "
                "Every other endpoint works without it."
            ),
        )

    failed_at = _rag_state.get("failed_at")
    if failed_at is not None:
        if time.monotonic() - failed_at < _RAG_RETRY_AFTER_S:
            raise HTTPException(status_code=503, detail=_rag_state["error"])
        _reset_rag_cache()

    if "retriever" not in _rag_state:
        try:
            _rag_state["retriever"] = rag.Retriever(chroma_dir=config.CHROMA_DIR)
            _rag_state["store"] = rag.SessionStore()
        except Exception as exc:
            msg = f"chat is unavailable: {exc}"
            _rag_state["error"] = msg
            _rag_state["failed_at"] = time.monotonic()
            log.warning(msg)
            raise HTTPException(status_code=503, detail=msg)
    return _rag_state["retriever"], _rag_state["store"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    from . import database

    if not os.path.exists(config.DB_PATH):
        log.info("no grid database, seeding %s", config.DB_PATH)
        database.init_db(config.DB_PATH)
        database.seed_city(config.DB_PATH, config.DEFAULT_CITY)
    yield


app = FastAPI(title="CanopyCast API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _corpus_ready() -> bool:
    """True only when the collection actually holds chunks.

    An empty chroma_db directory is created as a side effect of opening a
    client, so testing for the directory alone reported the corpus ready when
    nothing had been indexed.
    """
    try:
        import chromadb

        from .rag import COLLECTION_NAME

        client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
        return client.get_collection(COLLECTION_NAME).count() > 0
    except Exception:
        return False


@app.get("/")
def read_root():
    return {"service": "CanopyCast API", "docs": "/docs"}


@app.get("/api/health")
def health():
    """What the frontend polls to decide whether to use its offline fallback."""
    return {
        "status": "ok",
        "grid_ready": os.path.exists(config.DB_PATH),
        "corpus_ready": _corpus_ready(),
        "chat_ready": config.has_openai_key() and _corpus_ready(),
        "chat_model": config.CHAT_MODEL,
    }


@app.get("/api/city-grid", response_model=CityGrid)
def get_city_grid(city: str = config.DEFAULT_CITY):
    from . import database

    grid = database.get_city_grid(config.DB_PATH, city)
    if grid is None or not grid.cells:
        raise HTTPException(status_code=404, detail=f"no grid for {city}")
    return grid


@app.get("/api/cell-stats", response_model=Cell)
def get_cell_stats(lat: float, lon: float, city: str = config.DEFAULT_CITY):
    from . import database

    cell = database.get_cell_by_latlon(config.DB_PATH, city, lat, lon)
    if cell is None:
        raise HTTPException(status_code=404, detail="no cell at that coordinate")
    return cell


@app.post("/api/optimize", response_model=OptimizeResponse)
def run_optimization(req: OptimizeRequest):
    from . import database, optimize

    grid = database.get_city_grid(config.DB_PATH, req.city)
    if grid is None or not grid.cells:
        raise HTTPException(status_code=404, detail=f"no grid for {req.city}")
    return optimize.optimise(grid, top_n=req.top_n)


@app.get("/api/recommend-trees", response_model=RecommendResponse)
def recommend_trees(
    city: str = config.DEFAULT_CITY,
    cell_id: str | None = None,
    n: int = Query(default=3, ge=1, le=8),
):
    """Species suggestions as structured cards rather than chat prose.

    Same corpus as /api/chat. This returns fields the dashboard lays out;
    chat returns a paragraph for a human to read.
    """
    from . import database, rag

    retriever, _ = _get_rag()

    cell = None
    if cell_id is not None:
        cell = database.get_cell(config.DB_PATH, city, cell_id)
        if cell is None:
            raise HTTPException(status_code=404, detail=f"no cell {cell_id} in {city}")

    try:
        return rag.recommend_trees(city=city, cell=cell, retriever=retriever, n=n)
    except ValueError as exc:
        # The model returned something we could not parse into the schema.
        raise HTTPException(status_code=502, detail=f"recommendation failed: {exc}")
    except Exception as exc:
        log.exception("recommend-trees failed")
        raise HTTPException(status_code=502, detail=str(exc))


@app.post("/api/chat", response_model=ChatResponse)
def chatbot_interaction(req: ChatRequest):
    from . import rag

    retriever, store = _get_rag()
    try:
        return rag.answer(req, retriever=retriever, store=store)
    except Exception as exc:
        log.exception("chat failed")
        raise HTTPException(status_code=502, detail=str(exc))
