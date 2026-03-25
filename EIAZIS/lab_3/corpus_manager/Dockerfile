FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m nltk.downloader punkt averaged_perceptron_tagger averaged_perceptron_tagger_eng wordnet omw-1.4 && \
    python -m spacy download en_core_web_sm

COPY . .

RUN mkdir -p /app/uploads

EXPOSE 5000

CMD ["python", "app.py"]
