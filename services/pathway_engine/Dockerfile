FROM python:3.10-slim

WORKDIR /app

# Copy shared requirements or install specifically for Pathway
COPY services/pathway_engine/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt pathway

COPY services/pathway_engine /app/services/pathway_engine
COPY shared /app/shared

# Create data dir for CSV outputs
RUN mkdir -p /app/data

ENV PYTHONPATH=/app
EXPOSE 8080

CMD ["python", "services/pathway_engine/main.py"]
