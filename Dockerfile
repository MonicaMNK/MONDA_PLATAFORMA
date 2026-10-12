FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV MONDA_DEMO=0 COOKIE_SECURE=1
EXPOSE 8000
CMD ["sh","-c","alembic upgrade head && python -m backend.app.db.bootstrap && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
