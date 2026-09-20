# Build from the repo root so pyproject.toml / uv.lock are in context:
#   docker build -f days/day-003/Dockerfile -t day-003-chat .
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY days/day-003/app.py .

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
