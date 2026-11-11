FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Dependencies first: this layer is only rebuilt when requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Only the application code, never the whole folder.
COPY app/ app/

# Run as an unprivileged user.
RUN useradd --system --no-create-home appuser
USER appuser

EXPOSE 8000
# gunicorn listens on 0.0.0.0:$PORT. --preload creates the tables once, before the workers start.
CMD ["gunicorn", "--preload", "app.main:create_app()"]
