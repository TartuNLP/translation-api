FROM python:3.10-alpine

# Install system dependencies
RUN apk update && \
    apk add --no-cache \
        gcc \
        libffi-dev \
        musl-dev \
        git

ENV PYTHONIOENCODING=utf-8
WORKDIR /app

RUN adduser -D app && \
    chown -R app:app /app

USER app
ENV PATH="/home/app/.local/bin:${PATH}"

COPY --chown=app:app requirements.txt .
RUN pip install --no-cache-dir --upgrade --user -r requirements.txt && \
    rm requirements.txt

COPY --chown=app:app . .

EXPOSE 8000

ENTRYPOINT ["uvicorn", "app:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000",  "--log-config", "config/logging.prod.ini"]

