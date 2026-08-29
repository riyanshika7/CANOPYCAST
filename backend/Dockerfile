# -- builder: compile native wheels (chroma-hnswlib needs a C++ toolchain) ----
FROM python:3.11-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ libffi-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# -- runtime: slim image with no compiler ------------------------------------
FROM python:3.11-slim

# chroma-hnswlib links against libgomp (OpenMP) at runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgomp1 && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

# non-root user
RUN useradd --create-home appuser
WORKDIR /home/appuser/app

COPY app/ app/
COPY documents/ documents/

RUN chown -R appuser:appuser /home/appuser
USER appuser

# The SQLite grid database self-seeds on startup via the lifespan hook.
#
# The Chroma vector index is NOT built at image build time: it requires
# OPENAI_API_KEY which must never be baked into an image.  Run once at
# deploy time against a mounted volume:
#
#   docker run --rm -e OPENAI_API_KEY=... -v chroma_data:/home/appuser/app/chroma_db \
#       canopycast-api python -m app.ingest
#
# Without this step, /api/chat returns 503 while every other route works.

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request, os; port = os.environ.get('PORT', '8000'); urllib.request.urlopen(f'http://localhost:{port}/api/health')"
