# Built from the REPO ROOT, not ./backend.
#
# The control library lives in /controls at the repo root and is the
# product's content, not a test fixture — the application is useless without
# it. Building from ./backend left it out of the image entirely; that went
# unnoticed locally only because docker-compose bind-mounted it at the exact
# path the code happened to derive.
#
#   docker build -f backend/Dockerfile .

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    CONTROLS_DIR=/opt/assurelens/controls

WORKDIR /app

# Dependency layer first so application edits do not invalidate it.
#
# pyproject declares `packages = ["app"]`, and setuptools resolves that at
# install time — so installing before the source is copied fails with
# "package directory 'app' does not exist". The stub satisfies it; the real
# COPY below replaces it. Without this the whole dependency layer would have
# to be rebuilt on every source edit, which on Render's free tier is minutes
# per deploy.
#
# Runtime dependencies only: no pytest, ruff or mypy. Test tooling has no
# business in a deployed container.
COPY backend/pyproject.toml ./
RUN mkdir -p app && touch app/__init__.py \
    && pip install --upgrade pip \
    && pip install "."

COPY backend/ ./
COPY controls/ /opt/assurelens/controls/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
