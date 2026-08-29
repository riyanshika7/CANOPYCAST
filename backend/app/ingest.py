"""Corpus ingest pipeline for the urban forestry RAG.

Reads PDFs from backend/documents, cleans and chunks them with page provenance,
embeds via OpenAI, and persists into ChromaDB at backend/chroma_db in the
"forestry" collection. The shapes here are a contract for backend/app/rag.py.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import chromadb
from chromadb.api.models.Collection import Collection
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from pypdf import PdfReader


# Absolute, so it resolves the same from the repo root, from backend/, and
# from inside a marshal worktree. rag.py reads this exact directory.
CHROMA_DIR = str(Path(__file__).resolve().parent.parent / "chroma_db")
COLLECTION = "forestry"
EMBED_BATCH = 100
MIN_CHUNK_CHARS = 200
# A trailing run shorter than this is treated as a split word, not a whole one,
# unless it is one of the short words below that legitimately end a wrapped line.
_FRAGMENT_MAX_CHARS = 3
_SHORT_WORDS = frozenset(
    """a an as at be by do for he i if in is it its no nor of on or so the to up
    us we and are but can had has her him his how its may non not off our out per
    she that the them they this was who why you""".split()
)
EMBED_MODEL_ENV = "CANOPYCAST_EMBED_MODEL"
OPENAI_KEY_ENV = "OPENAI_API_KEY"
DEFAULT_EMBED_MODEL = "text-embedding-3-small"

CHUNK_SIZE = 1800
CHUNK_OVERLAP = 250
SPLIT_SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " ", ""]


DOC_META: dict[str, tuple[str, str]] = {
    "delhi_green_action_plan.pdf": ("Delhi Green Action Plan", "Delhi"),
    "bengaluru_urban_forest_manual_2025.pdf": (
        "Bengaluru Urban Forest Manual 2025",
        "Bengaluru",
    ),
    "punjab_urban_greening_policy.pdf": (
        "Punjab Urban Greening Policy",
        "Punjab",
    ),
    "wb_tpofa_guidelines.pdf": ("West Bengal TPOFA Guidelines", "Kolkata"),
    # The four municipal PDFs are procedural. None of them names a species
    # suited to Kolkata, so a question about what to plant here retrieved
    # Delhi and Bengaluru chunks. This reference closes that gap.
    "kolkata_avenue_trees.md": ("Avenue Trees for Kolkata", "Kolkata"),
}


_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=SPLIT_SEPARATORS,
)


_DOT_LEADER_RE = re.compile(r"\.{3,}")
_MULTISPACE_RE = re.compile(r"[ \t\f\v]+")
_MULTINEW_RE = re.compile(r"\n{3,}")
# Bare page number on its own line, e.g. "2", " 2 ", "  3  "
_BARE_PAGE_RE = re.compile(r"^\s*\d{1,4}\s*$", re.MULTILINE)
# A lone single-letter token wedged between letter characters: the PDF column
# reflow split one word across two visual positions. The stray letter belongs to
# the word on its RIGHT, so keep the left space and close the right one:
# "objective o f" -> "objective of", "provide s hade" -> "provide shade".
# Closing both sides instead would give "objectiveof", which is a worse token
# than the one it replaced.
# "a" and "I" are real one-letter words, so gluing them wrecks ordinary prose:
# "and a minimum" became "andaminimum" across 300+ places in the corpus, which
# poisons the BM25 tokens. Skip those two and glue only true reflow fragments.
_SINGLE_LETTER_GLUE = re.compile(
    r"(?<=[A-Za-z(])\s(?![aAI]\s)([A-Za-z])\s(?=[A-Za-z)])"
)
# Bracket followed by a word with no separating space: ")may" -> ") may"
_BRACKET_WORD = re.compile(r"\)(?=[A-Za-z])")
# Word followed by ")" with separating space: "ha )" -> "ha)"
_WORD_BRACKET = re.compile(r"(?<=[A-Za-z])\s+\)")


def normalise_text(text: str) -> str:
    """Clean text extracted from a single PDF page.

    Fixes the recurring defects in our forestry corpus:
      * broken hyphenation across line breaks ("nation -\nwide")
      * column-reflow word splits ("Br uhat", "objective o f", "provide s")
      * table-of-contents dot leaders (".......")
      * bare page numbers and excessive whitespace
    """
    if not text:
        return ""

    out = text.replace("\r\n", "\n").replace("\r", "\n")

    # drop table-of-contents dot leaders (and surrounding whitespace)
    out = _DOT_LEADER_RE.sub(" ", out)
    # strip bare page-number lines that recur as running headers
    out = _BARE_PAGE_RE.sub("", out)

    # line-by-line fixups: PDF extraction places one visual line per "\n",
    # so cross-line defects are easiest to handle here.
    out = _join_broken_lines(out)
    # then in-line cleanups within what's now a single paragraph
    out = _SINGLE_LETTER_GLUE.sub(r" \1", out)
    out = _WORD_BRACKET.sub(")", out)
    out = _BRACKET_WORD.sub(") ", out)

    # collapse runs of whitespace
    out = _MULTISPACE_RE.sub(" ", out)
    # collapse 3+ blank lines into a single paragraph break
    out = _MULTINEW_RE.sub("\n\n", out)

    return out.strip()


def _join_broken_lines(text: str) -> str:
    """Repair line-break induced word splits.

    Three patterns recur in the corpus:
      * "nation -\\nwide."   trailing hyphen with space before it (syllable
        split; drop the hyphen)
      * "sub-\\ncomponent"   trailing hyphen glued to the previous letter
        (compound word; keep the hyphen)
      * "Br\\nuhat Bengaluru" line ends mid-word with no hyphen (column
        reflow; glue without a space)
    """
    lines = text.split("\n")
    out: list[str] = []
    for line in lines:
        if not out:
            out.append(line)
            continue
        prev = out[-1]
        # syllable-split hyphen: previous line ends with whitespace+hyphen
        m_drop = re.search(r"[ \t]+\-$", prev)
        if m_drop:
            out[-1] = prev[: m_drop.start()] + line.lstrip()
            continue
        # compound hyphen: previous line ends with a letter then hyphen
        m_keep = re.search(r"[A-Za-z]\-$", prev)
        if m_keep:
            out[-1] = prev + line.lstrip()
            continue
        # Line ends with a letter and the next starts with one. That is USUALLY
        # ordinary word wrapping, not a split word: measured over the corpus this
        # case fires 1959 times and 86% of them end in a complete word. Gluing
        # them all turned "and an excellent" into "anexcellent". So join with a
        # space by default, and only glue when the trailing fragment is too
        # short to be a word, which is the column-reflow case ("Br" + "uhat").
        if prev and prev[-1].isalpha() and line and line[0].isalpha():
            fragment = re.split(r"\s", prev)[-1]
            split_word = (
                len(fragment) < _FRAGMENT_MAX_CHARS
                and fragment.lower() not in _SHORT_WORDS
            )
            joiner = "" if split_word else " "
            out[-1] = prev + joiner + line.lstrip()
            continue
        out.append(line)
    return "\n".join(out)


def load_pdf(path: str | Path) -> list[tuple[int, str]]:
    """Read a PDF and return (1-indexed page_number, page_text) pairs."""
    reader = PdfReader(str(path))
    pages: list[tuple[int, str]] = []
    for i, page in enumerate(reader.pages):
        raw = page.extract_text() or ""
        pages.append((i + 1, normalise_text(raw)))
    return pages


def load_markdown(path: str | Path) -> list[tuple[int, str]]:
    """Read a markdown file into (section_number, text) pairs.

    Markdown has no pages, so each top-level section becomes one unit and its
    index stands in for a page number. A citation then points at a section
    rather than at the whole file.
    """
    text = Path(path).read_text(encoding="utf-8")
    sections: list[tuple[int, str]] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("## ") and current:
            sections.append((len(sections) + 1, normalise_text("\n".join(current))))
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append((len(sections) + 1, normalise_text("\n".join(current))))
    return sections


def load_document(path: str | Path) -> list[tuple[int, str]]:
    """Dispatch to the loader for this file type."""
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        return load_pdf(path)
    if suffix in (".md", ".txt"):
        return load_markdown(path)
    raise ValueError(f"unsupported document type: {suffix}")


def chunk_document(
    pages: list[tuple[int, str]],
    doc_title: str,
    source_file: str,
    city: str,
) -> list[dict]:
    """Split a document's pages into chunks while preserving the start page.

    Splits page by page so each chunk knows the page number it began on. Chunks
    shorter than MIN_CHUNK_CHARS after cleaning are dropped as page furniture.
    """
    chunks: list[dict] = []
    chunk_index = 0
    for page_num, page_text in pages:
        if not page_text:
            continue
        for piece in _splitter.split_text(page_text):
            piece = piece.strip()
            if len(piece) < MIN_CHUNK_CHARS:
                continue
            chunks.append(
                {
                    "text": piece,
                    "doc_title": doc_title,
                    "source_file": source_file,
                    "page": page_num,
                    "city": city,
                    "chunk_index": chunk_index,
                    "id": f"{source_file}:{chunk_index}",
                }
            )
            chunk_index += 1
    return chunks


def _build_default_client() -> OpenAI:
    api_key = os.environ.get(OPENAI_KEY_ENV)
    if not api_key:
        raise RuntimeError(
            f"{OPENAI_KEY_ENV} is not set; export it before embedding."
        )
    return OpenAI(api_key=api_key)


def embed_texts(
    texts: list[str], client: OpenAI | None = None
) -> list[list[float]]:
    """Embed a list of texts using the OpenAI embeddings API.

    The client is injectable so tests can pass a fake. When client is None we
    build one from os.environ and raise a clear RuntimeError if the API key is
    missing. Calls are batched at EMBED_BATCH per request.
    """
    if not texts:
        return []
    client = client or _build_default_client()
    model = os.environ.get(EMBED_MODEL_ENV, DEFAULT_EMBED_MODEL)

    vectors: list[list[float]] = []
    for start in range(0, len(texts), EMBED_BATCH):
        batch = texts[start : start + EMBED_BATCH]
        resp = client.embeddings.create(model=model, input=batch)
        for item in resp.data:
            vectors.append(list(item.embedding))
    return vectors


def _get_collection(client: chromadb.PersistentClient | None = None) -> Collection:
    client = client or chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection(
        name=COLLECTION, metadata={"hnsw:space": "cosine"}
    )


def build_index(
    documents_dir: str | Path,
    chroma_dir: str | Path = CHROMA_DIR,
    client: chromadb.PersistentClient | None = None,
    embed_client=None,
) -> int:
    """Build the persistent Chroma index from every known document."""
    client = client or chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_or_create_collection(
        name=COLLECTION, metadata={"hnsw:space": "cosine"}
    )

    documents_dir = Path(documents_dir)
    total = 0
    for source_file in sorted(DOC_META):
        path = documents_dir / source_file
        if not path.exists():
            continue
        doc_title, city = DOC_META[source_file]
        pages = load_document(path)
        chunks = chunk_document(pages, doc_title, source_file, city)
        if not chunks:
            continue
        vectors = embed_texts([c["text"] for c in chunks], client=embed_client)
        collection.upsert(
            ids=[c["id"] for c in chunks],
            documents=[c["text"] for c in chunks],
            embeddings=vectors,
            metadatas=[
                {
                    "doc_title": c["doc_title"],
                    "source_file": c["source_file"],
                    "page": c["page"],
                    "city": c["city"],
                    "chunk_index": c["chunk_index"],
                }
                for c in chunks
            ],
        )
        total += len(chunks)
    return total


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    backend_root = here.parent
    docs = backend_root / "documents"
    n = build_index(docs, chroma_dir=backend_root / "chroma_db")
    print(f"Indexed {n} chunks into {COLLECTION} at {CHROMA_DIR}")