FROM python:3.11.7-slim-bookworm

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies using binary wheels (no compilation needed)
# psycopg2-binary includes pre-compiled PostgreSQL bindings, so no gcc/libpq-dev needed
RUN pip install --upgrade pip && \
    pip install --only-binary :all: -r requirements.txt

# Copy application code
COPY bot/ ./bot/

# Run the bot
CMD ["python", "-m", "bot.main"]
