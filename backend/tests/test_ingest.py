"""Tests for app.ingest. The whole suite must pass with no OPENAI_API_KEY.

We never instantiate the real OpenAI client. Every test that needs embeddings
injects a fake that records the inputs and returns deterministic vectors.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

# Ensure no real key leaks in. Even though we never call the real client, a
# stray OPENAI_API_KEY in CI would defeat the purpose of these tests.
# Removal now happens for the whole suite in tests/conftest.py.

from app import ingest  # noqa: E402


class FakeEmbeddingsAPI:
    """Stand-in for the OpenAI embeddings client used in tests.

    Mirrors the real client shape: client.embeddings.create(model=..., input=...).
    Records every input it sees and returns one deterministic vector per input.
    Vector length is 8 to keep assertions small but real values matter: the
    Chroma client must accept whatever shape we hand it.
    """

    def __init__(self, dim: int = 8) -> None:
        self.dim = dim
        self.calls: list[list[str]] = []
        self.embeddings = self._EmbeddingsNamespace(self)

    class _Resp:
        def __init__(self, dim: int, n: int) -> None:
            self.data = [
                type("Item", (), {"embedding": [float(i + 1)] * dim})()
                for i in range(n)
            ]

    class _EmbeddingsNamespace:
        def __init__(self, parent: "FakeEmbeddingsAPI") -> None:
            self._parent = parent

        def create(self, model, input):  # noqa: A002
            texts = list(input)
            self._parent.calls.append(texts)
            return FakeEmbeddingsAPI._Resp(self._parent.dim, len(texts))


@pytest.fixture
def fake_embeddings() -> FakeEmbeddingsAPI:
    return FakeEmbeddingsAPI()


# ----- normalise_text -----


def test_normalise_fixes_hyphenation_across_linebreaks():
    raw = "The initiative now operates across multiple cities nation -\nwide."
    assert "nationwide" in ingest.normalise_text(raw)
    assert "nation -" not in ingest.normalise_text(raw)


def test_normalise_fixes_hyphenation_without_space():
    raw = "sub-\ncomponent of the West Bengal"
    out = ingest.normalise_text(raw)
    assert "sub-component" in out
    assert "sub-\n" not in out


def test_normalise_joins_soft_split_words():
    # The corpus defect is "Br\nuhat" (column reflow across a line break),
    # not "Br uhat" on one line. The line-break version is what _join_broken_lines
    # fixes reliably without false positives on real two-letter words.
    raw = "Byelaws within the meaning of Section 318 of the Br\nuhat Bengaluru"
    out = ingest.normalise_text(raw)
    assert "Bruhat" in out
    assert "Br\nuhat" not in out


def test_normalise_joins_orphan_letter_token():
    # Stray single letter token, e.g. "objective o f mitigating".
    raw = "objective o f mitigating the biotic pressure"
    out = ingest.normalise_text(raw)
    # The stray letter belongs to the word on its right. Closing both sides
    # would give "objectiveof", which is a worse token than the original.
    assert "objective of" in out
    assert "o f " not in out


def test_normalise_joins_split_after_close_bracket():
    raw = "notional area of 0.25 ha )may be considered"
    out = ingest.normalise_text(raw)
    assert ") may" in out
    assert ")may" not in out


def test_normalise_strips_table_of_contents_dot_leaders():
    raw = "1. Introduction: ............... 3\n2. Agencies: .... 4"
    out = ingest.normalise_text(raw)
    assert "...." not in out
    assert "Introduction:" in out
    assert "3" in out


def test_normalise_drops_bare_page_number_lines():
    raw = "Department of Forests\n\n2 \n\nContents\n\nReal body text."
    out = ingest.normalise_text(raw)
    lines = [ln.strip() for ln in out.split("\n") if ln.strip()]
    assert "2" not in lines
    assert "Contents" in out
    assert "Real body text." in out


def test_normalise_collapses_whitespace_runs():
    raw = "line   one\n\n\n\n\nline     two\t\t\tthree"
    out = ingest.normalise_text(raw)
    assert "   " not in out
    assert "\n\n\n" not in out
    assert "line one" in out
    assert "line two" in out


def test_normalise_handles_empty_input():
    assert ingest.normalise_text("") == ""


# ----- load_pdf -----


def test_load_pdf_returns_one_indexed_tuple_per_page(tmp_path: Path):
    # craft a tiny PDF on the fly so we have a deterministic count
    from pypdf import PdfWriter

    pdf_path = tmp_path / "tiny.pdf"
    writer = PdfWriter()
    for _ in range(3):
        writer.add_blank_page(width=72, height=72)
    with pdf_path.open("wb") as fh:
        writer.write(fh)

    pages = ingest.load_pdf(pdf_path)
    assert [p for p, _ in pages] == [1, 2, 3]
    # each entry has text (possibly empty for blank pages) but is normalised
    for _, text in pages:
        assert text == text.strip()


# ----- chunk_document -----


def test_chunk_document_carries_starting_page():
    pages = [
        (1, "alpha " * 500),
        (2, "beta " * 500),
        (3, "gamma " * 500),
    ]
    chunks = ingest.chunk_document(pages, "Doc", "doc.pdf", "Kolkata")
    assert chunks, "expected at least one chunk from long pages"
    # chunk_index is monotonic and ids are unique
    indexes = [c["chunk_index"] for c in chunks]
    assert indexes == sorted(indexes)
    assert len(set(indexes)) == len(indexes)
    # every chunk knows which page it started on
    for c in chunks:
        assert c["page"] in {1, 2, 3}
        assert c["doc_title"] == "Doc"
        assert c["source_file"] == "doc.pdf"
        assert c["city"] == "Kolkata"
        assert c["id"] == f"doc.pdf:{c['chunk_index']}"
        assert len(c["text"]) >= ingest.MIN_CHUNK_CHARS


def test_chunk_document_drops_short_page_furniture():
    pages = [
        (1, "x" * 50),  # below MIN_CHUNK_CHARS, must be dropped
        (2, "real content " * 200),  # long enough
    ]
    chunks = ingest.chunk_document(pages, "Doc", "doc.pdf", "Kolkata")
    assert chunks
    assert all(len(c["text"]) >= ingest.MIN_CHUNK_CHARS for c in chunks)


# ----- embed_texts -----


def test_embed_texts_uses_injected_client(fake_embeddings: FakeEmbeddingsAPI):
    out = ingest.embed_texts(["hello", "world"], client=fake_embeddings)
    assert len(out) == 2
    assert all(len(v) == fake_embeddings.dim for v in out)
    assert fake_embeddings.calls == [["hello", "world"]]


def test_embed_texts_batches_at_one_hundred(fake_embeddings: FakeEmbeddingsAPI):
    texts = [f"chunk {i}" for i in range(230)]
    out = ingest.embed_texts(texts, client=fake_embeddings)
    assert len(out) == 230
    # 100 + 100 + 30 = three batches
    assert [len(c) for c in fake_embeddings.calls] == [100, 100, 30]


def test_embed_texts_empty_input_returns_empty(fake_embeddings: FakeEmbeddingsAPI):
    assert ingest.embed_texts([], client=fake_embeddings) == []
    assert fake_embeddings.calls == []


def test_embed_texts_raises_clear_error_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError) as exc:
        ingest.embed_texts(["hello"])
    assert "OPENAI_API_KEY" in str(exc.value)


# ----- build_index -----


def test_build_index_end_to_end(
    tmp_path: Path, monkeypatch, fake_embeddings: FakeEmbeddingsAPI
):
    # stage two real PDFs and a fake openai client via monkeypatching
    src_docs = Path(__file__).resolve().parent.parent / "documents"
    docs = tmp_path / "documents"
    docs.mkdir()
    (docs / "wb_tpofa_guidelines.pdf").write_bytes(
        (src_docs / "wb_tpofa_guidelines.pdf").read_bytes()
    )
    (docs / "punjab_urban_greening_policy.pdf").write_bytes(
        (src_docs / "punjab_urban_greening_policy.pdf").read_bytes()
    )
    chroma_dir = tmp_path / "chroma_db"

    # route the default-client builder through our fake so embed_texts
    # (called without client=) still avoids the network
    monkeypatch.setattr(ingest, "_build_default_client", lambda: fake_embeddings)

    n = ingest.build_index(docs, chroma_dir=chroma_dir)
    assert n > 0

    # Re-open the collection from disk and confirm metadata contract
    import chromadb

    client = chromadb.PersistentClient(path=str(chroma_dir))
    coll = client.get_collection(ingest.COLLECTION)
    assert coll.count() == n

    sample = coll.get(limit=3, include=["metadatas", "embeddings"])
    required = {"doc_title", "source_file", "page", "city", "chunk_index"}
    for meta in sample["metadatas"]:
        assert required.issubset(meta.keys())
        assert isinstance(meta["doc_title"], str)
        assert isinstance(meta["source_file"], str)
        assert isinstance(meta["page"], int)
        assert meta["city"] in {"Kolkata", "Delhi", "Bengaluru", "Punjab", "General"}
        assert isinstance(meta["chunk_index"], int)
    # embeddings must be the ones our fake produced. Chroma stores them as
    # float32 so values lose a few ULPs of precision; check structure and
    # that the expected set of distinct vectors round-trips intact.
    assert sample["embeddings"].shape == (3, fake_embeddings.dim)
    distinct = {float(v[0]) for v in sample["embeddings"]}
    expected = {1.0, 2.0, 3.0}
    assert {round(v, 3) for v in distinct} == expected


def test_build_index_skips_missing_documents(
    tmp_path: Path, monkeypatch, fake_embeddings: FakeEmbeddingsAPI
):
    docs = tmp_path / "documents"
    docs.mkdir()
    chroma_dir = tmp_path / "chroma_db"
    monkeypatch.setattr(ingest, "_build_default_client", lambda: fake_embeddings)
    assert ingest.build_index(docs, chroma_dir=chroma_dir) == 0

class TestOneLetterWordsSurvive:
    """The reflow glue used to eat real one-letter words.

    "and a minimum" became "andaminimum" in 300+ places, which turns a
    searchable phrase into a junk BM25 token.
    """

    def test_article_a_is_not_glued(self):
        assert ingest.normalise_text("How a roadside species is chosen") == (
            "How a roadside species is chosen"
        )
        assert ingest.normalise_text("and a minimum of two rows") == "and a minimum of two rows"

    def test_pronoun_i_is_not_glued(self):
        assert ingest.normalise_text("where I noted the gap") == "where I noted the gap"

    def test_reflow_letter_attaches_to_the_word_on_its_right(self):
        assert ingest.normalise_text("provide s hade for the street") == (
            "provide shade for the street"
        )
        assert ingest.normalise_text("the objective o f the plan") == (
            "the objective of the plan"
        )

    def test_wrapped_lines_join_with_a_space(self):
        assert ingest.normalise_text("and an\nexcellent tree") == "and an excellent tree"
        assert ingest.normalise_text("planted in\nthe median") == "planted in the median"

    def test_true_column_split_joins_without_a_space(self):
        assert ingest.normalise_text("Br\nuhat Bengaluru") == "Bruhat Bengaluru"


class TestMarkdownSource:
    def test_sections_become_pages(self, tmp_path):
        doc = tmp_path / "d.md"
        doc.write_text("# Title\n\nintro para\n\n## One\n\nbody one\n\n## Two\n\nbody two\n")
        sections = ingest.load_markdown(doc)
        assert [n for n, _ in sections] == [1, 2, 3]
        assert "body one" in sections[1][1]

    def test_load_document_dispatches_on_suffix(self, tmp_path):
        doc = tmp_path / "d.md"
        doc.write_text("# T\n\n" + "x " * 200)
        assert ingest.load_document(doc)
        with pytest.raises(ValueError, match="unsupported"):
            ingest.load_document(tmp_path / "d.docx")


class TestKolkataSpeciesCoverage:
    """The four municipal PDFs are procedural and name no Kolkata species.

    Without a Kolkata-tagged species source, "what should I plant here"
    retrieves Delhi and Bengaluru chunks while the city boost pushes the
    other way. This guards the source that closes the gap.
    """

    def test_kolkata_source_names_the_demo_species(self):
        docs = Path(__file__).resolve().parents[1] / "documents"
        path = docs / "kolkata_avenue_trees.md"
        if not path.exists():
            pytest.skip("corpus not present")
        chunks = ingest.chunk_document(
            ingest.load_document(path), "Avenue Trees for Kolkata", path.name, "Kolkata"
        )
        blob = " ".join(c["text"] for c in chunks).lower()
        for species in ("neem", "azadirachta", "gulmohar", "bakul", "peepal"):
            assert species in blob, f"{species} missing from the Kolkata source"
        assert all(c["city"] == "Kolkata" for c in chunks)


def test_every_registered_document_exists():
    """A typo in DOC_META is skipped silently by build_index, so the corpus
    loses a source and nothing reports it."""
    from pathlib import Path

    from app import config
    from app.ingest import DOC_META

    missing = [
        name for name in DOC_META
        if not (Path(config.DOCUMENTS_DIR) / name).exists()
    ]
    assert missing == []


def test_kolkata_sources_outnumber_a_single_outside_manual():
    """The corpus was 5 Kolkata chunks against 386 from Bengaluru, which is
    what pushed local answers out of the retrieval window."""
    from app.ingest import DOC_META

    kolkata = [n for n, (_, city) in DOC_META.items() if city == "Kolkata"]
    assert len(kolkata) >= 4
