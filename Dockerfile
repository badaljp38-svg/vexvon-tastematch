FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000 BIND_HOST=0.0.0.0
WORKDIR /app
COPY server.py ./
COPY static/ ./static/
RUN useradd --system --uid 10001 appuser
USER appuser
EXPOSE 8000
CMD ["python", "server.py"]
