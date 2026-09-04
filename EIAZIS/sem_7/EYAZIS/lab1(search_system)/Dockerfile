FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords')"

COPY . .

ENV PYTHONUNBUFFERED=1
ENV WATCH_DIRECTORY=/app/documents

EXPOSE 5001

CMD ["python", "app.py"]
