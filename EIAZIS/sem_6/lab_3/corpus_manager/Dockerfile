FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install  -r requirements.txt && \
    python -m nltk.downloader punkt averaged_perceptron_tagger averaged_perceptron_tagger_eng wordnet omw-1.4 && \
    pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

COPY . .

RUN mkdir -p /app/uploads

EXPOSE 5000

CMD ["python", "app.py"]
