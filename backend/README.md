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

## Building the corpus index

Chat needs a Chroma index over `documents/`. It costs a fraction of a cent to build
and only has to run once.

```bash
cp .env.example .env      # then fill in OPENAI_API_KEY
python -m app.ingest
```

Without it, `/api/chat` returns 503 and `/api/health` reports `chat_ready: false`.
Every other endpoint works without an API key.

## Retrieval

Dense vectors from Chroma are fused with BM25 lexical search using Reciprocal Rank
Fusion. Lexical is not optional: queries are dominated by exact species tokens
(Neem, Azadirachta indica, Krishnachura) that dense embeddings blur together.

Answers are grounded in the selected map cell, so the same question against a
41 C bare block and a shaded park block gives different advice.
