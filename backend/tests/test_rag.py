import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.rag import Retriever, SessionStore, answer
from app.schema import Cell, ChatRequest


class FakeCollection:
    def __init__(self, records, dense_order):
        self.ids = [r[0] for r in records]
        self.documents = [r[1] for r in records]
        self.metadatas = [r[2] for r in records]
        self.dense_order = list(dense_order)
        self.get_calls = 0

    def get(self, include=None, limit=None, offset=0, **kwargs):
        self.get_calls += 1
        start = offset or 0
        end = start + limit if limit is not None else None
        return {
            "ids": self.ids[start:end],
            "documents": self.documents[start:end],
            "metadatas": [dict(m) for m in self.metadatas[start:end]],
        }

    def query(self, query_embeddings=None, n_results=12, include=None, **kwargs):
        id_set = set(self.ids)
        picked = [i for i in self.dense_order if i in id_set][:n_results]
        idx = {doc_id: n for n, doc_id in enumerate(self.ids)}
        return {
            "ids": [picked],
            "documents": [[self.documents[idx[i]] for i in picked]],
            "metadatas": [[self.metadatas[idx[i]] for i in picked]],
        }


class FakeClient:
    def __init__(self, chat_content="Plant Neem at 5 m spacing (WB Manual)."):
        self.chat_content = chat_content
        self.messages = None
        self.embeddings = self
        self.chat = SimpleNamespace(completions=self)

    def create(self, model=None, input=None, messages=None, **kwargs):
        if messages is not None:
            self.messages = messages
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content=self.chat_content)
                    )
                ]
            )
        return SimpleNamespace(data=[SimpleNamespace(embedding=[0.1, 0.2, 0.3])])


def _records():
    return [
        (
            "a",
            "Neem Azadirachta indica is a native shade tree. Plant at 5 metre spacing.",
            {
                "doc_title": "WB Urban Forestry Guidelines",
                "source_file": "wb_tpofa_guidelines.pdf",
                "page": 4,
                "city": "Kolkata",
                "chunk_index": 0,
            },
        ),
        (
            "b",
            "Rain gardens and soil moisture in temperate zones xyzunique densehit token.",
            {
                "doc_title": "Temperate Handbook",
                "source_file": "other.pdf",
                "page": 1,
                "city": "General",
                "chunk_index": 1,
            },
        ),
        (
            "c",
            "Coastal palm belts on sand only, no inland shade species.",
            {
                "doc_title": "Coastal Palms",
                "source_file": "coast.pdf",
                "page": 9,
                "city": "Mumbai",
                "chunk_index": 2,
            },
        ),
        (
            "d",
            "Gulmohar Krishnachura Delonix regia flowers in hot streets. Crown 8 metres.",
            {
                "doc_title": "Bengaluru Urban Forest Manual",
                "source_file": "bengaluru.pdf",
                "page": 12,
                "city": "General",
                "chunk_index": 3,
            },
        ),
    ]


def _cell():
    return Cell(
        cell_id="3_5",
        x=3,
        y=5,
        lat=22.5726,
        lon=88.3639,
        base_temperature=38.7,
        canopy_cover=11.5,
        population_density="High",
        park_proximity_km=1.4,
    )


def test_rrf_ranks_overlap_above_single():
    # Dense ranks b first then a; BM25 on "Neem" ranks only a. Overlap should win.
    coll = FakeCollection(_records(), dense_order=["b", "a", "c", "d"])
    retriever = Retriever(collection=coll, client=FakeClient())
    hits = retriever.search("Neem", city=None, k=5)
    assert hits, "expected fused hits"
    assert hits[0]["doc_title"] == "WB Urban Forestry Guidelines"
    assert "Neem" in hits[0]["text"]
    titles = [h["doc_title"] for h in hits]
    if "Temperate Handbook" in titles:
        assert titles.index("WB Urban Forestry Guidelines") < titles.index(
            "Temperate Handbook"
        )


def test_bm25_corpus_built_once():
    coll = FakeCollection(_records(), dense_order=["a", "b"])
    retriever = Retriever(collection=coll, client=FakeClient())
    bm25 = retriever._bm25
    calls = coll.get_calls
    assert calls >= 1
    retriever.search("Neem")
    retriever.search("Gulmohar Krishnachura")
    assert coll.get_calls == calls
    assert retriever._bm25 is bm25


def test_session_keeps_last_six_turns():
    store = SessionStore()
    for i in range(8):
        store.append("s1", "user", f"m{i}")
    session = store.get("s1")
    assert len(session.turns) == 6
    assert [t[1] for t in session.turns] == [f"m{i}" for i in range(2, 8)]


def test_session_prunes_on_ttl():
    store = SessionStore()
    store.append("old", "user", "stale")
    store._sessions["old"].last_seen = time.time() - 4000
    store.get("fresh")
    assert "old" not in store._sessions
    store.append("expiring", "user", "bye")
    store._sessions["expiring"].last_seen = time.time() - 4000
    revived = store.get("expiring")
    assert revived.turns == []


def test_answer_prompt_includes_cell_numbers():
    coll = FakeCollection(_records(), dense_order=["a", "d", "b"])
    client = FakeClient()
    retriever = Retriever(collection=coll, client=client)
    store = SessionStore()
    cell = _cell()
    req = ChatRequest(
        message="What native tree should I plant here?",
        session_id="sess-1",
        city="Kolkata",
        selected_cell=cell,
    )
    resp = answer(req, retriever, store, client=client)
    blob = " ".join(m["content"] for m in client.messages)
    assert "38.7" in blob
    assert "11.5" in blob
    assert "High" in blob
    assert "1.4" in blob
    assert resp.response
    ctx = store.get("sess-1").planning_context
    assert ctx["base_temperature"] == 38.7


def test_citations_capped_at_200_chars():
    long_text = "Neem Azadirachta indica. " + ("care watering mulch " * 40)
    assert len(long_text) > 200
    records = [
        (
            "long",
            long_text,
            {
                "doc_title": "Long Manual",
                "source_file": "long.pdf",
                "page": 3,
                "city": "Kolkata",
                "chunk_index": 0,
            },
        )
    ]
    coll = FakeCollection(records, dense_order=["long"])
    client = FakeClient()
    retriever = Retriever(collection=coll, client=client)
    req = ChatRequest(message="Neem spacing", session_id="s", city="Kolkata")
    resp = answer(req, retriever, SessionStore(), client=client)
    assert resp.citations
    assert all(len(c.snippet) <= 200 for c in resp.citations)


def test_answer_requires_openai_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    coll = FakeCollection(_records(), dense_order=["a"])
    retriever = Retriever(collection=coll, client=FakeClient())
    req = ChatRequest(message="Neem", session_id="s", city="Kolkata")
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        answer(req, retriever, SessionStore(), client=None)
