# rebuild v3
FROM python:3.11-slim 


WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements-prod.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY alembic.ini ./
COPY seed_plans.sql.sql ./
COPY start.sh ./
RUN chmod +x start.sh

# Expose port
EXPOSE 8001

# Run migrations then start FastAPI
CMD ["./start.sh"]
