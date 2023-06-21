FROM python:3.10

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    \
    POETRY_VERSION=1.2.1 \
    POETRY_HOME="/opt/poetry" \
    PATH="${PATH}:/opt/poetry/bin/" \
    POETRY_NO_INTERACTION=1

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PREFECT_FLOW_DIR=/app/prefect_flows/

COPY ./prefect-flows/poetry.lock prefect-flows/pyproject.toml ./
COPY ./prefect-flows/prefect_flows ./prefect_flows
COPY ./prefect-utils /prefect-utils

RUN poetry config virtualenvs.create false && \
    poetry install --only main
