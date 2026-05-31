FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app
COPY services/orchestrator/requirements.txt .
RUN pip install --progress=plain -r requirements.txt

# Pre-download sentence-transformers model to avoid timeout during first run
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

COPY services/orchestrator .
COPY shared ./shared

CMD ["python", "-u", "app/main.py"]
