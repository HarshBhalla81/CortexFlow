FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app
COPY services/orchestrator/requirements.txt .
RUN pip install -r requirements.txt

COPY services/orchestrator .
COPY shared ./shared

CMD ["python", "-u", "app/main.py"]