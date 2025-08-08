# Backend (FastAPI)
Run:
```
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Deploy on Render with start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
