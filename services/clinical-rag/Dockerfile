FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

# Install CPU-only torch first to avoid the 2GB CUDA build
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -r requirements.txt

# Pre-download embedding model into the image layer so no network call at runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

COPY app ./app

EXPOSE 8085

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8085"]
