"""Hybrid retrieval, session memory, and grounded answering for CanopyCast."""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from pydantic import ValidationError
from rank_bm25 import BM25Okapi

# Same reason as ingest: loads backend/.env so this module works when it is
# imported outside the server.
from . import config  # noqa: F401

from .budget import BUDGET
from .schema import (
    Cell,
    ChatRequest,
    ChatResponse,
    Citation,
    RecommendResponse,
    TreeRecommendation,
)

RRF_K = 60
PER_SIDE = 12
DEFAULT_K = 5
TURN_LIMIT = 6
SNIPPET_CHARS = 200
CITY_BOOST = 2.0
# No single document may supply more than this many of the k returned chunks.
MAX_PER_DOC = 2
CHROMA_DIR = Path(__file__).resolve().parent.parent / "chroma_db"
COLLECTION_NAME = "forestry"
_TOKEN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


# The SDK default is a 10 minute timeout, which for a chat route means a demo
# that appears frozen rather than one that reports a failure.
REQUEST_TIMEOUT_S = 45.0
MAX_RETRIES = 2


def _real_openai_client():
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    from openai import OpenAI

    return OpenAI(api_key=key, timeout=REQUEST_TIMEOUT_S, max_retries=MAX_RETRIES)


def _real_collection(chroma_dir=None):
    import chromadb

    chroma = chromadb.PersistentClient(path=str(chroma_dir or CHROMA_DIR))
    return chroma.get_collection(COLLECTION_NAME)


def _snippet(text: str, n: int = SNIPPET_CHARS) -> str:
    return " ".join(text.split())[:n]


def _rrf(rank_lists: list[list[str]]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranked in rank_lists:
        for rank, doc_id in enumerate(ranked, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (RRF_K + rank)
    return scores


def _cell_dict(cell: Cell | dict | None) -> dict:
    if cell is None:
        return {}
    if isinstance(cell, dict):
        return cell
    return cell.model_dump()


def _round(value, places: int = 1):
    """Round for display. Raw floats carry 15 decimals, which is noise."""
    return round(value, places) if isinstance(value, (int, float)) else value


def _format_cell(data: dict) -> str:
    return (
        f"cell_id: {data.get('cell_id')}\n"
        f"temperature_c: {_round(data.get('base_temperature'))}\n"
        f"canopy_cover_percent: {_round(data.get('canopy_cover'))}\n"
        f"population_density: {data.get('population_density')}\n"
        f"park_proximity_km: {_round(data.get('park_proximity_km'), 2)}"
    )


class Retriever:
    """Lexical BM25 pins exact species tokens (Neem, Azadirachta indica, Gulmohar, Krishnachura) that dense embeddings smear together."""

    def __init__(self, collection=None, client=None, chroma_dir=None):
        self._client = client
        if collection is None:
            collection = _real_collection(chroma_dir)
        self.collection = collection
        self._ids: list[str] = []
        self._docs: list[str] = []
        self._metas: list[dict] = []
        self._by_id: dict[str, tuple[str, dict]] = {}
        self._bm25: BM25Okapi | None = None
        self._load_bm25()

    def _load_bm25(self) -> None:
        ids, docs, metas = [], [], []
        offset, batch = 0, 500
        while True:
            chunk = self.collection.get(
                include=["documents", "metadatas"], limit=batch, offset=offset
            )
            got = chunk.get("ids") or []
            if not got:
                break
            ids.extend(got)
            docs.extend(chunk.get("documents") or [])
            metas.extend(chunk.get("metadatas") or [])
            if len(got) < batch:
                break
            offset += batch
        self._ids = ids
        self._docs = docs
        self._metas = [m or {} for m in metas]
        self._by_id = {
            doc_id: (text, meta)
            for doc_id, text, meta in zip(self._ids, self._docs, self._metas)
        }
        tokenized = [_tokenize(text) for text in self._docs]
        # Empty corpus has no IDF; skip BM25 rather than crash at load.
        self._bm25 = BM25Okapi(tokenized) if tokenized else None

    def _openai(self):
        if self._client is None:
            self._client = _real_openai_client()
        return self._client

    def _embed(self, query: str) -> list[float]:
        model = os.environ.get("CANOPYCAST_EMBED_MODEL", "text-embedding-3-small")
        # Every chat turn embeds the query, so this counts against the same
        # ceiling as the completion it precedes.
        BUDGET.check()
        resp = self._openai().embeddings.create(model=model, input=query)
        BUDGET.record(resp)
        return resp.data[0].embedding

    def _dense_ids(self, query: str, n: int) -> list[str]:
        if not self._ids:
            return []
        raw = self.collection.query(
            query_embeddings=[self._embed(query)],
            n_results=min(n, len(self._ids)),
            include=["documents", "metadatas"],
        )
        ids = (raw.get("ids") or [[]])[0]
        return list(ids)

    def _bm25_ids(self, query: str, n: int) -> list[str]:
        if self._bm25 is None or not self._ids:
            return []
        tokens = _tokenize(query)
        if not tokens:
            return []
        scores = self._bm25.get_scores(tokens)
        ranked = sorted(
            range(len(scores)), key=lambda i: float(scores[i]), reverse=True
        )
        out = []
        for i in ranked:
            if float(scores[i]) <= 0:
                break
            out.append(self._ids[i])
            if len(out) >= n:
                break
        return out

    def _hit(self, doc_id: str) -> dict:
        text, meta = self._by_id[doc_id]
        return {
            "text": text,
            "doc_title": meta.get("doc_title", ""),
            "source_file": meta.get("source_file", ""),
            "page": int(meta.get("page", 0) or 0),
            "city": meta.get("city", ""),
            "chunk_index": int(meta.get("chunk_index", 0) or 0),
        }

    def search(self, query: str, city: Optional[str] = None, k: int = DEFAULT_K) -> list[dict]:
        dense = self._dense_ids(query, PER_SIDE)
        lexical = self._bm25_ids(query, PER_SIDE)
        scores = _rrf([dense, lexical])
        if city:
            # Prefer in-city and General chunks; do not drop outsiders.
            for doc_id in list(scores):
                chunk_city = (self._by_id.get(doc_id, ("", {}))[1] or {}).get("city", "")
                if chunk_city in (city, "General"):
                    scores[doc_id] *= CITY_BOOST
        ordered = sorted(scores, key=lambda d: scores[d], reverse=True)
        return [self._hit(doc_id) for doc_id in self._cap_per_doc(ordered, k)]

    def _cap_per_doc(self, ordered: list[str], k: int) -> list[str]:
        """Keep at most MAX_PER_DOC chunks from any one document.

        The Kolkata source is 5 chunks against 386 from Bengaluru, so the city
        boost lifted the same three chunks to the top of every query and pushed
        out the maintenance and approval pages that actually answered some of
        them. Capping keeps the local source present without letting it own the
        whole window. Overflow is appended only if the cap leaves room spare.
        """
        picked: list[str] = []
        overflow: list[str] = []
        seen: dict[str, int] = {}
        for doc_id in ordered:
            if doc_id not in self._by_id:
                continue
            title = (self._by_id[doc_id][1] or {}).get("doc_title", "")
            if seen.get(title, 0) < MAX_PER_DOC:
                seen[title] = seen.get(title, 0) + 1
                picked.append(doc_id)
                if len(picked) == k:
                    return picked
            elif len(overflow) < k:
                overflow.append(doc_id)
        return (picked + overflow)[:k]


@dataclass
class Session:
    session_id: str
    turns: list[tuple[str, str]] = field(default_factory=list)
    planning_context: dict = field(default_factory=dict)
    last_seen: float = field(default_factory=time.time)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def prune(self, ttl_s: float = 3600) -> None:
        now = time.time()
        dead = [sid for sid, s in self._sessions.items() if now - s.last_seen > ttl_s]
        for sid in dead:
            del self._sessions[sid]

    def get(self, session_id: str) -> Session:
        self.prune()
        session = self._sessions.get(session_id)
        if session is None:
            session = Session(session_id=session_id)
            self._sessions[session_id] = session
        session.last_seen = time.time()
        return session

    def append(self, session_id: str, role: str, text: str) -> None:
        session = self.get(session_id)
        session.turns.append((role, text))
        session.turns = session.turns[-TURN_LIMIT:]
        session.last_seen = time.time()

    def set_context(self, session_id: str, cell: Cell | dict | None) -> None:
        session = self.get(session_id)
        session.planning_context = _cell_dict(cell)
        session.last_seen = time.time()


def _system_prompt(city: str, has_cell: bool) -> str:
    text = (
        f"You are CanopyCast, an urban forestry advisor for {city}. "
        "Answer only from the provided manual excerpts. "
        f"Name specific native species suited to {city}. "
        "When excerpts give planting spacing or care, use those concrete numbers; "
        "if they do not cover something, say so plainly and do not invent a figure. "
        "Cite by referring to the document by name in the prose. "
        "Keep the answer under 120 words; the panel is small."
    )
    if has_cell:
        text += (
            " A map cell is selected. The answer must be hyper-local to that cell, not generic. "
            "You are given its temperature, canopy cover percent, population density, and park distance. "
            "You must reason about those specific numbers when recommending species and planting."
        )
    return text


def _user_payload(req: ChatRequest, cell_data: dict, chunks: list[dict]) -> str:
    parts = [f"City: {req.city}"]
    if cell_data:
        parts.append("Selected cell stats:\n" + _format_cell(cell_data))
        parts.append(
            "Reason about these exact cell numbers (temperature, canopy_cover, "
            "population_density, park_proximity_km). Do not give generic advice."
        )
    excerpts = []
    for i, chunk in enumerate(chunks, start=1):
        excerpts.append(
            f"[{chunk.get('doc_title', 'document')}, p.{chunk.get('page', 0)}]\n"
            f"{chunk.get('text', '')}"
        )
    if excerpts:
        parts.append("Manual excerpts:\n" + "\n\n".join(excerpts))
    else:
        parts.append("Manual excerpts:\n(none retrieved)")
    parts.append("Question:\n" + req.message)
    return "\n\n".join(parts)


# A planner clicks a cell and asks "which trees should we plant here". The words
# that carry the meaning are on the map, not in the sentence, so the raw message
# retrieves on "trees" and "plant" alone and matches consent letters and nursery
# procedure. Expanding the query with the selection is what makes the retrieval
# local. Kept short: long expansions drown the user's own words in BM25.
_CANOPY_LOW_PCT = 25.0
_HOT_CELSIUS = 38.0


def _query_expansion(city: Optional[str], cell_data: dict | None) -> list[str]:
    terms: list[str] = []
    if city:
        terms.append(city)
    if not cell_data:
        return terms
    canopy = cell_data.get("canopy_cover")
    if isinstance(canopy, (int, float)) and canopy < _CANOPY_LOW_PCT:
        terms.append("shade canopy cover")
    temperature = cell_data.get("base_temperature")
    if isinstance(temperature, (int, float)) and temperature > _HOT_CELSIUS:
        terms.append("heat tolerant")
    return terms


def _search_query(
    message: str,
    turns: list[tuple[str, str]],
    city: Optional[str] = None,
    cell_data: dict | None = None,
) -> str:
    prior = [text for role, text in turns if role == "user"]
    expansion = _query_expansion(city, cell_data)
    return " ".join(prior + [message] + expansion).strip()


def answer(
    req: ChatRequest,
    retriever: Retriever,
    store: SessionStore,
    client=None,
) -> ChatResponse:
    session = store.get(req.session_id)
    if req.selected_cell is not None:
        store.set_context(req.session_id, req.selected_cell)
        session = store.get(req.session_id)
    cell_data = _cell_dict(req.selected_cell) or session.planning_context
    chunks = retriever.search(
        _search_query(req.message, session.turns, req.city, cell_data),
        city=req.city,
        k=DEFAULT_K,
    )
    messages = [{"role": "system", "content": _system_prompt(req.city, bool(cell_data))}]
    for role, text in session.turns:
        messages.append({"role": role, "content": text})
    messages.append({"role": "user", "content": _user_payload(req, cell_data, chunks)})
    if client is None:
        client = _real_openai_client()
    model = os.environ.get("CANOPYCAST_CHAT_MODEL", "gpt-5.6-luna")
    BUDGET.check()
    resp = client.chat.completions.create(model=model, messages=messages)
    BUDGET.record(resp)
    text = (resp.choices[0].message.content or "").strip()
    store.append(req.session_id, "user", req.message)
    store.append(req.session_id, "assistant", text)
    citations = [
        Citation(
            doc_title=str(chunk.get("doc_title", "")),
            page=int(chunk.get("page", 0) or 0),
            snippet=_snippet(chunk.get("text", "")),
        )
        for chunk in chunks
    ]
    return ChatResponse(response=text, citations=citations)


_HEIGHT_NUM = re.compile(r"(\d+(?:\.\d+)?)")


def _parse_height_ft(value) -> Optional[float]:
    # Corpus writes "about 40 feet"; a guessed height would look measured.
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = _HEIGHT_NUM.search(str(value))
    if not match:
        return None
    return float(match.group(1))


def _chunk_citation(chunk: dict) -> Citation:
    return Citation(
        doc_title=str(chunk.get("doc_title", "")),
        page=int(chunk.get("page", 0) or 0),
        snippet=_snippet(chunk.get("text", "")),
    )


def _recommend_query(city: str, cell_data: dict) -> str:
    parts = [city, "native species", "avenue tree", "shade", "spacing"]
    if cell_data:
        for key in (
            "base_temperature",
            "canopy_cover",
            "population_density",
            "park_proximity_km",
        ):
            val = cell_data.get(key)
            if val is not None:
                parts.append(str(val))
    return " ".join(parts)


def _recommend_system_prompt(city: str, has_cell: bool, n: int) -> str:
    text = (
        f"You are CanopyCast, an urban forestry advisor for {city}. "
        "Return STRICT JSON: a top-level object with a 'recommendations' key "
        f"holding a list of at most {n} tree recommendations. "
        "JSON mode requires an object, not a bare array. "
        "Each item has common_name, botanical_name (string or null), crown_shape, "
        "mature_height_ft (number or null), why_here, caution. "
        "You MUST only name species that actually appear in the retrieved excerpts. "
        "Inventing a species is a failure. "
        "mature_height_ft must be a number taken from the excerpts, or null. Do not guess."
    )
    if has_cell:
        text += (
            " A map cell is selected. why_here MUST reference that cell's actual "
            "temperature, canopy cover percent, and population density numbers. "
            "Do not give generic city-wide advice."
        )
    else:
        text += (
            " No map cell is selected. Give general city advice and say so plainly "
            "in why_here."
        )
    return text


def _recommend_user_payload(
    city: str, cell_data: dict, chunks: list[dict], n: int
) -> str:
    parts = [f"City: {city}", f"Return at most {n} recommendations."]
    if cell_data:
        parts.append("Selected cell stats:\n" + _format_cell(cell_data))
        parts.append(
            "why_here must cite these exact cell numbers (temperature, canopy_cover, "
            "population_density)."
        )
    else:
        parts.append("No cell is selected. Give general city advice and say so.")
    excerpts = []
    for chunk in chunks:
        excerpts.append(
            f"[{chunk.get('doc_title', 'document')}, p.{chunk.get('page', 0)}]\n"
            f"{chunk.get('text', '')}"
        )
    if excerpts:
        parts.append("Manual excerpts:\n" + "\n\n".join(excerpts))
    else:
        parts.append("Manual excerpts:\n(none retrieved)")
    parts.append(
        "Respond with JSON: {\"recommendations\": [ ... ]} using only species "
        "named in the excerpts."
    )
    return "\n\n".join(parts)


def _parse_recommendation_rows(text: str) -> list:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"unparseable JSON from model: {exc}") from exc
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        rows = data.get("recommendations", [])
        if rows is None:
            return []
        if isinstance(rows, list):
            return rows
        raise ValueError("recommendations is not a list")
    raise ValueError("JSON must be an object or array")


def _citations_for_species(
    common_name: str, botanical_name: Optional[str], chunks: list[dict]
) -> list[Citation]:
    names = [n.lower() for n in (common_name, botanical_name) if n]
    if not names:
        return []
    found: list[Citation] = []
    for chunk in chunks:
        hay = str(chunk.get("text", "")).lower()
        if any(name in hay for name in names):
            found.append(_chunk_citation(chunk))
    return found


def _row_to_recommendation(raw, chunks: list[dict]) -> Optional[TreeRecommendation]:
    if not isinstance(raw, dict):
        return None
    payload = {
        "common_name": raw.get("common_name"),
        "botanical_name": raw.get("botanical_name"),
        "crown_shape": raw.get("crown_shape"),
        "mature_height_ft": _parse_height_ft(raw.get("mature_height_ft")),
        "why_here": raw.get("why_here"),
        "caution": raw.get("caution"),
    }
    try:
        rec = TreeRecommendation.model_validate(payload)
    except ValidationError:
        return None
    rec.citations = _citations_for_species(
        rec.common_name, rec.botanical_name, chunks
    )
    return rec


def recommend_trees(
    city,
    cell,
    retriever,
    client=None,
    n=3,
) -> RecommendResponse:
    cell_data = _cell_dict(cell)
    chunks = retriever.search(_recommend_query(city, cell_data), city=city, k=DEFAULT_K)
    messages = [
        {
            "role": "system",
            "content": _recommend_system_prompt(city, bool(cell_data), n),
        },
        {
            "role": "user",
            "content": _recommend_user_payload(city, cell_data, chunks, n),
        },
    ]
    if client is None:
        client = _real_openai_client()
    model = os.environ.get("CANOPYCAST_CHAT_MODEL", "gpt-5.6-luna")
    BUDGET.check()
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
    )
    BUDGET.record(resp)
    text = (resp.choices[0].message.content or "").strip()
    rows = _parse_recommendation_rows(text)
    recs: list[TreeRecommendation] = []
    for raw in rows:
        rec = _row_to_recommendation(raw, chunks)
        if rec is not None:
            recs.append(rec)
        if len(recs) >= n:
            break
    sources = [_chunk_citation(chunk) for chunk in chunks]
    return RecommendResponse(
        city=city,
        cell_id=cell_data.get("cell_id") if cell_data else None,
        recommendations=recs,
        sources=sources,
    )
