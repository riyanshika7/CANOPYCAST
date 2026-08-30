import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.rag import (
    MAX_PER_DOC,
    Retriever,
    SessionStore,
    _query_expansion,
    _search_query,
    answer,
    recommend_trees,
)
from app.schema import Cell, ChatRequest, TreeRecommendation


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


def _neem_rec(**overrides):
    row = {
        "common_name": "Neem",
        "botanical_name": "Azadirachta indica",
        "crown_shape": "roundish",
        "mature_height_ft": 40,
        "why_here": "Hot cell at 38.7 C with 11.5 percent canopy needs dense shade.",
        "caution": "brittle branches in storms",
    }
    row.update(overrides)
    return row


def _gulmohar_rec(**overrides):
    row = {
        "common_name": "Gulmohar",
        "botanical_name": "Delonix regia",
        "crown_shape": "umbrella",
        "mature_height_ft": None,
        "why_here": "Avenue tree for hot streets with low canopy.",
        "caution": None,
    }
    row.update(overrides)
    return row


def test_recommend_trees_maps_well_formed_with_citations():
    payload = {"recommendations": [_neem_rec()]}
    client = FakeClient(chat_content=json.dumps(payload))
    retriever = Retriever(
        collection=FakeCollection(_records(), dense_order=["a", "d", "b"]),
        client=client,
    )
    resp = recommend_trees("Kolkata", _cell(), retriever, client=client, n=3)
    assert len(resp.recommendations) == 1
    rec = resp.recommendations[0]
    assert isinstance(rec, TreeRecommendation)
    assert rec.common_name == "Neem"
    assert rec.botanical_name == "Azadirachta indica"
    assert rec.citations, "species citations should come from retrieved chunks"
    assert rec.citations[0].doc_title == "WB Urban Forestry Guidelines"
    assert rec.citations[0].page == 4
    assert rec.citations[0].snippet
    assert len(rec.citations[0].snippet) <= 200
    assert resp.sources
    assert {s.doc_title for s in resp.sources} >= {"WB Urban Forestry Guidelines"}
    assert resp.city == "Kolkata"
    assert resp.cell_id == "3_5"


def test_recommend_trees_skips_malformed_entry():
    payload = {
        "recommendations": [
            _neem_rec(),
            {"common_name": 123, "why_here": None},
            _gulmohar_rec(),
        ]
    }
    client = FakeClient(chat_content=json.dumps(payload))
    retriever = Retriever(
        collection=FakeCollection(_records(), dense_order=["a", "d", "b"]),
        client=client,
    )
    resp = recommend_trees("Kolkata", None, retriever, client=client, n=3)
    names = [r.common_name for r in resp.recommendations]
    assert names == ["Neem", "Gulmohar"]


def test_recommend_unparseable_json_raises_value_error():
    client = FakeClient(chat_content="this is not json {")
    retriever = Retriever(
        collection=FakeCollection(_records(), dense_order=["a"]),
        client=client,
    )
    with pytest.raises(ValueError) as ei:
        recommend_trees("Kolkata", None, retriever, client=client)
    assert type(ei.value) is ValueError
    assert "JSON" in str(ei.value) or "json" in str(ei.value).lower()


def test_recommend_bare_json_array_is_handled():
    client = FakeClient(chat_content=json.dumps([_neem_rec(), _gulmohar_rec()]))
    retriever = Retriever(
        collection=FakeCollection(_records(), dense_order=["a", "d"]),
        client=client,
    )
    resp = recommend_trees("Kolkata", None, retriever, client=client, n=3)
    assert [r.common_name for r in resp.recommendations] == ["Neem", "Gulmohar"]


def test_recommend_prompt_includes_cell_numbers():
    client = FakeClient(chat_content=json.dumps({"recommendations": []}))
    retriever = Retriever(
        collection=FakeCollection(_records(), dense_order=["a", "d", "b"]),
        client=client,
    )
    recommend_trees("Kolkata", _cell(), retriever, client=client)
    blob = " ".join(m["content"] for m in client.messages)
    assert "38.7" in blob
    assert "11.5" in blob
    assert "High" in blob


def test_recommend_parses_height_about_40_feet_and_missing():
    payload = {
        "recommendations": [
            _neem_rec(mature_height_ft="about 40 feet"),
            _gulmohar_rec(mature_height_ft=None),
        ]
    }
    client = FakeClient(chat_content=json.dumps(payload))
    retriever = Retriever(
        collection=FakeCollection(_records(), dense_order=["a", "d"]),
        client=client,
    )
    resp = recommend_trees("Kolkata", None, retriever, client=client)
    by_name = {r.common_name: r for r in resp.recommendations}
    assert by_name["Neem"].mature_height_ft == 40.0
    assert by_name["Gulmohar"].mature_height_ft is None


def _stub_by_id(spec):
    """spec: list of (doc_id, doc_title). Builds the _by_id shape search uses."""
    return {doc_id: ("text for " + doc_id, {"doc_title": title, "page": 1})
            for doc_id, title in spec}


def test_cap_per_doc_limits_one_document():
    r = Retriever.__new__(Retriever)
    r._by_id = _stub_by_id([(f"a{i}", "Big Manual") for i in range(6)]
                           + [("b0", "Kolkata Doc"), ("c0", "Punjab Doc")])
    # k=4 is exactly what the cap can supply from three documents, so nothing
    # is backfilled and the cap is visible on its own.
    picked = r._cap_per_doc([f"a{i}" for i in range(6)] + ["b0", "c0"], k=4)
    titles = [r._by_id[d][1]["doc_title"] for d in picked]
    assert titles.count("Big Manual") == MAX_PER_DOC
    assert "Kolkata Doc" in titles and "Punjab Doc" in titles


def test_cap_per_doc_backfills_rather_than_returning_fewer():
    # Capping must never shrink the window: k=5 from the same three documents
    # can only be filled by going back over the capped document.
    r = Retriever.__new__(Retriever)
    r._by_id = _stub_by_id([(f"a{i}", "Big Manual") for i in range(6)]
                           + [("b0", "Kolkata Doc"), ("c0", "Punjab Doc")])
    picked = r._cap_per_doc([f"a{i}" for i in range(6)] + ["b0", "c0"], k=5)
    assert len(picked) == 5
    assert len(set(picked)) == 5


def test_cap_per_doc_backfills_when_short():
    # Only one document exists, so the cap must not return fewer than k.
    r = Retriever.__new__(Retriever)
    r._by_id = _stub_by_id([(f"a{i}", "Only Doc") for i in range(5)])
    assert len(r._cap_per_doc([f"a{i}" for i in range(5)], k=5)) == 5


def test_query_expansion_needs_a_cell():
    assert _query_expansion("Kolkata", None) == ["Kolkata"]
    assert _query_expansion(None, None) == []


def test_query_expansion_reflects_cell_conditions():
    hot_bare = _query_expansion("Kolkata", {"canopy_cover": 4.0, "base_temperature": 41.7})
    assert "shade canopy cover" in hot_bare and "heat tolerant" in hot_bare
    cool_green = _query_expansion("Kolkata", {"canopy_cover": 60.0, "base_temperature": 30.0})
    assert cool_green == ["Kolkata"]


def test_search_query_grounds_a_deictic_question():
    # "plant here" carries no retrievable terms; the cell has to supply them.
    q = _search_query("what should we plant here", [], "Kolkata",
                      {"canopy_cover": 4.0, "base_temperature": 41.7})
    assert q.startswith("what should we plant here")
    assert "Kolkata" in q and "heat tolerant" in q


class _FakeStreamClient:
    """Mimics the shape of an OpenAI streaming response."""

    def __init__(self, pieces):
        self._pieces = pieces
        self.chat = self

    @property
    def completions(self):
        return self

    def create(self, model, messages, stream=False, **kwargs):
        assert stream is True
        def gen():
            for piece in self._pieces:
                delta = type("D", (), {"content": piece})()
                choice = type("C", (), {"delta": delta})()
                yield type("E", (), {"choices": [choice]})()
        return gen()


def test_answer_stream_yields_tokens_then_one_citations_event():
    from app.rag import answer_stream

    retriever = Retriever(collection=FakeCollection(_records(), dense_order=['a','b','c','d']), client=FakeClient())
    store = SessionStore()
    req = ChatRequest(message="what to plant", session_id="s1", city="Kolkata")
    events = list(answer_stream(req, retriever=retriever, store=store,
                                client=_FakeStreamClient(["Plant ", "Neem."])))
    kinds = [k for k, _ in events]
    assert kinds == ["token", "token", "citations"]


def test_answer_stream_records_history_for_the_next_turn():
    from app.rag import answer_stream

    store = SessionStore()
    req = ChatRequest(message="what to plant", session_id="s2", city="Kolkata")
    list(answer_stream(req, retriever=Retriever(collection=FakeCollection(_records(), dense_order=['a','b','c','d']), client=FakeClient()), store=store,
                       client=_FakeStreamClient(["Bakul."])))
    turns = store.get("s2").turns
    assert turns[-2:] == [("user", "what to plant"), ("assistant", "Bakul.")]
