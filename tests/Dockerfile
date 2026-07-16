FROM --platform=linux/amd64 python:3.11-slim
WORKDIR /app

COPY tests/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn" , "tests.api:app" , "--host" , "0.0.0.0" , "--port" , "8001"]