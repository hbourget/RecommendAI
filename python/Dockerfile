# python/Dockerfile
FROM python:3.8-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY function.py .

FROM python:3.8

COPY --from=builder /app /app

WORKDIR /app

CMD ["python", "function.py"]
