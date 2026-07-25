FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create .env for collectstatic build step (overridden by runtime env)
RUN printf "SECRET_KEY=docker-build-only-not-for-production\nDEBUG=False\nALLOWED_HOSTS=.onrender.com,localhost,127.0.0.1\nCSRF_TRUSTED_ORIGINS=https://*.onrender.com\nDATABASE_URL=sqlite:///db.sqlite3\n" > .env && \
    python manage.py collectstatic --noinput --clear && \
    rm .env

CMD python manage.py migrate --noinput && gunicorn Hello.wsgi:application --bind 0.0.0.0:8000 --workers 2 --threads 4 --timeout 60 --access-logfile - --log-level info