FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV SECRET_KEY=docker-build-only-not-for-production
ENV DEBUG=False
ENV ALLOWED_HOSTS=.onrender.com,localhost,127.0.0.1
ENV CSRF_TRUSTED_ORIGINS=https://*.onrender.com
ENV DATABASE_URL=sqlite:///db.sqlite3

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput --clear

CMD ["gunicorn", "Hello.wsgi:application", "--bind", "0.0.0.0:8000"]