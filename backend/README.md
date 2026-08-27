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
