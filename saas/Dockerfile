FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app . .
RUN DJANGO_DEBUG=false \
    DJANGO_SECRET_KEY=build-only-not-a-runtime-secret \
    DATABASE_URL=postgresql://jobmail:build-only@localhost:5432/jobmail \
    python manage.py collectstatic --noinput

COPY --chown=app:app deploy/oci/start.sh /usr/local/bin/start-jobmail
RUN chmod 0755 /usr/local/bin/start-jobmail

USER app
EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/start-jobmail"]
