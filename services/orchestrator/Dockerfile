FROM python:3.11-slim

WORKDIR /app

COPY services/orchestrator/requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

COPY services/orchestrator /app/services/orchestrator
COPY shared /app/shared

ENV PYTHONPATH=/app/services/orchestrator:/app
WORKDIR /app/services/orchestrator

CMD ["python", "-u", "app/main.py"]
