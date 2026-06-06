FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app
COPY services/orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/orchestrator/requirements-ai.txt .
RUN pip install --no-cache-dir -r requirements-ai.txt

COPY services/orchestrator/requirements-ai.txt .
RUN pip install --no-cache-dir -r requirements-watchdog.txt

RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

COPY services/orchestrator .
COPY shared ./shared

CMD ["python", "-u", "app/main.py"]
