FROM --platform=linux/amd64 python:3.11-slim
WORKDIR /app

COPY services/gateway/requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY services/gateway /app/services/gateway
COPY shared /app/shared

ENV PYTHONPATH=/app/services/gateway:/app
WORKDIR /app/services/gateway

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]