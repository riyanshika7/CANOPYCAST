"""CanopyCast API.

Routes are thin. The grid lives in database.py, the scoring in optimize.py,
and retrieval plus answering in rag.py.
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .schema import (
    Cell,
    ChatRequest,
    ChatResponse,
    CityGrid,
    OptimizeRequest,
    OptimizeResponse,
)

log = logging.getLogger("canopycast")

# The retriever loads a Chroma collection and builds a BM25 corpus, which is
# slow and needs an API key. Chat is the only route that wants it, so it is
# built on first use and a failure degrades that one route instead of the app.
_rag_state: dict = {}


def _get_rag():
    from . import rag

    if "error" in _rag_state:
        raise HTTPException(status_code=503, detail=_rag_state["error"])
    if "retriever" not in _rag_state:
        try:
            _rag_state["retriever"] = rag.Retriever(chroma_dir=config.CHROMA_DIR)
            _rag_state["store"] = rag.SessionStore()
        except Exception as exc:
            msg = f"chat is unavailable: {exc}"
            _rag_state["error"] = msg
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


@app.get("/")
def read_root():
    return {"service": "CanopyCast API", "docs": "/docs"}


@app.get("/api/health")
def health():
    """What the frontend polls to decide whether to use its offline fallback."""
    return {
        "status": "ok",
        "grid_ready": os.path.exists(config.DB_PATH),
        "corpus_ready": os.path.exists(config.CHROMA_DIR),
        "chat_ready": config.has_openai_key() and os.path.exists(config.CHROMA_DIR),
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


@app.post("/api/chat", response_model=ChatResponse)
def chatbot_interaction(req: ChatRequest):
    from . import rag

    retriever, store = _get_rag()
    try:
        return rag.answer(req, retriever=retriever, store=store)
    except Exception as exc:
        log.exception("chat failed")
        raise HTTPException(status_code=502, detail=str(exc))
