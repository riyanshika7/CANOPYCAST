# CanopyCast

Interactive, map-based planning tool for combating Urban Heat Islands.

Pick a city block on the map, see its heat and canopy stats, run an optimizer
that ranks where planting trees would do the most good, and ask an assistant
what to plant there. The assistant answers from real municipal forestry
manuals and cites the document and page.

## Layout

```
backend/     FastAPI, SQLite grid, optimizer, RAG    (Chirag)
frontend/    React, Leaflet map, dashboard, chatbot  (Nitesh, Riyanshika)
```

## Running it

Backend:

```bash
cd backend
python -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/uvicorn app.main:app --reload
```

The grid seeds itself on first start. Docs at http://127.0.0.1:8000/docs

Frontend:

```bash
cd frontend
npm install && npm run dev
```

Chat and tree recommendations additionally need an OpenAI key and a one-off
index build. See `backend/README.md`. Without them those two routes return 503
and `/api/health` reports `chat_ready: false`; everything else works.

## How the pieces fit

The grid is synthetic but not random. It is generated from named spatial
features, urban cores and green anchors like the Maidan and the East Kolkata
Wetlands, so heat falls off with distance and canopy runs opposite to it. It is
seeded, so the map is identical on every run.

The optimizer scores every cell on four normalised terms: heat, canopy deficit,
population, and corridor connectivity. The corridor term is the interesting
one. It scores the gap between two green spaces highest and scores near zero
both inside a park and far from everything, because planting in a park adds
nothing and planting in the middle of nowhere links nothing.

The assistant uses hybrid retrieval, dense vectors fused with BM25. Lexical
search matters here because the questions are exact species names, which dense
embeddings blur together. Answers are grounded in whichever cell is selected,
so the same question gives different advice on a bare 41 C block than on a
shaded one.
