FROM python:3.13-slim
WORKDIR /app
COPY server/ server/
COPY site/ site/
ENV DB_PATH=/data/scrabble.db SITE_DIR=/app/site PORT=8000 PYTHONUNBUFFERED=1
EXPOSE 8000
USER nobody
CMD ["python", "server/app.py"]
