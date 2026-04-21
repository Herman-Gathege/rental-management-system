FROM python:3.11-slim

WORKDIR /app

# System deps (for psycopg2)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client
    
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000