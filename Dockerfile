FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY backend/requirements.runtime.txt /tmp/requirements.runtime.txt

RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements.runtime.txt

COPY --chown=app:app backend /app/backend
COPY --chown=app:app alembic /app/alembic
COPY --chown=app:app alembic.ini /app/alembic.ini

USER app

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
