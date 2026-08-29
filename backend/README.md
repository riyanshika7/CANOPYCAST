# CanopyCast Backend

FastAPI backend providing synthetic city grid statistics, micro-climate optimization scoring, and urban forestry RAG recommendations.

## 🚀 Setup & Installation

1.  **Create virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run Development Server:**
    ```bash
    uvicorn app.main:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000`. Documentation at `http://127.0.0.1:8000/docs`.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | readiness flags the frontend polls before falling back offline |
| GET | `/api/city-grid?city=Kolkata` | the full 20x20 grid |
| GET | `/api/cell-stats?lat=&lon=` | stats for the cell containing a point |
| POST | `/api/optimize` | top planting sites with score breakdown and impact |
| GET | `/api/recommend-trees` | species suggestions as structured cards |
| POST | `/api/chat` | grounded RAG answer with page citations |

## Chat request shape

```json
{
  "message": "what should I plant here",
  "session_id": "uuid generated once per page load",
  "city": "Kolkata",
  "selected_cell": { "...": "a Cell from /api/cell-stats, or null" }
}
```

Returns `{ "response": "...", "citations": [{ "doc_title", "page", "snippet" }] }`.

## Recommend vs chat

Both read the same corpus. `/api/chat` returns prose for a person to read.
`/api/recommend-trees?city=Kolkata&cell_id=8_13&n=3` returns fields the sidebar
lays out as cards:

```json
{ "recommendations": [{
    "common_name": "Bakul", "botanical_name": "Mimusops elengi",
    "crown_shape": "roundish", "mature_height_ft": 40.0,
    "why_here": "Dense dome crown suits a 41.7 C block at 4 percent canopy.",
    "caution": null, "citations": [ ... ] }] }
```

The model is constrained to species that appear in the retrieved excerpts. A
row that fails validation is dropped and the rest are kept, so one malformed
entry cannot fail the whole request.

## Building the corpus index

Chat needs a Chroma index over `documents/`. It costs a fraction of a cent to build
and only has to run once.

```bash
cp .env.example .env      # then fill in OPENAI_API_KEY
python -m app.ingest
```

Without it, `/api/chat` returns 503 and `/api/health` reports `chat_ready: false`.
Every other endpoint works without an API key.

To exercise the retrieval pipeline before a key exists, build the index with
offline hashed vectors:

```bash
python -m app.ingest --fake-embeddings
```

That indexes all 507 chunks and makes chunking, storage, BM25, fusion and
citations work for real. The vectors carry no meaning, so dense ranking is
not representative and answer quality from such an index proves nothing.
Never record the demo against it.

## Retrieval

Dense vectors from Chroma are fused with BM25 lexical search using Reciprocal Rank
Fusion. Lexical is not optional: queries are dominated by exact species tokens
(Neem, Azadirachta indica, Krishnachura) that dense embeddings blur together.

Answers are grounded in the selected map cell, so the same question against a
41 C bare block and a shaded park block gives different advice.

## Container

```bash
docker build -t canopycast-api .
docker run -p 8000:8000 canopycast-api
```

Binds `$PORT` if the host sets one, which Render and Railway both do.

Built and run: the image comes up healthy in about 2 seconds, serves the grid
and optimizer, runs as a non-root user, and honours $PORT. It is 879 MB, most
of which is chromadb and its native dependencies.

The index is deliberately not baked into the image, since building it needs an
API key. Run it once at deploy time against a mounted volume:

```bash
docker run --rm -e OPENAI_API_KEY=... \
  -v chroma_data:/home/appuser/app/chroma_db \
  canopycast-api python -m app.ingest
```
