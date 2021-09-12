# Machine Translation API

A Flask API for using TartuNLP's public NMT engines. The API is designed to be used together with our 
[translation workers](https://github.com/TartuNLP/translation-worker).

The project is developed by the [NLP research group](https://tartunlp.ai) at the [Universty of Tartu](https://ut.ee).
Neural machine translation can also be tested in our [web demo](https://translate.ut.ee/).

## API usage

The API can be used with the following request:

POST `/translatio/v2`

HEADERS (optional):

```
x-api-key = public
```

BODY (json):

```
{
     "text": "Tere",
     "src": "et",
     "tgt": "en",
     "domain": "auto",
     "application": "test-application"
}
```

Response:

```
{
    "result": "Hi."
}
```

In case the text field contains a string, it is automatically split into sentences, which are translated and merged into
a single string. In case it contains a list, the service assumes this list to be a list of sentences and will not do any
further splitting.

Some parameters, such as the source language and domain may be optional, depending on the exact engine. The optional
`x-api-key` header is used to map requests to the models of a specific workspace and is mostly only necessary when using
[custom models](https://translate.ut.ee/collaboration). The optional `application` parameter is only used by certain
custom models to apply custom preprocessing for requests from integrated CAT tools, such as
[MemoQ](https://github.com/TartuNLP/MemoQ-Neurotolge-Plugin),
[SDL](https://github.com/TartuNLP/SDL-Neurotolge-Plugin) or Memsource.

To use older version of the API, use the following POST request format:

POST `/translation/v1`

Query parameters:
```
olang = est
odomain = auto
auth = public
```

BODY (JSON):

```
{
    "text": "Tere.",
}
```

Upon which the server returns the translation in a JSON:
```
{
    "result": "Hi."
}
```

The `olang` and `odomain` parameters are for the output language and output domain. The `auth` field is like the 
`x-api-key` header in the newer version.

## Setup

The API can be deployed using the docker image published alongside the repository. Each image version correlates to
a specific release. The API is designed to work together with our
[translation worker](https://github.com/TartuNLP/translation-worker) worker containers and RabbitMQ.

The service is available on port `5000`. Logs are stored in `/app/logs/`. Logging configuration is loaded from
`/app/config/logging.ini` and service configuration from `/app/config/config.yaml` files.

The container uses Gunicorn to run the API. Gunicorn parameters can be modified with environment variables where
the variable name is capitalized and the prefix `GUNICORN_` is added. For example, the number of workers can be modified
as follows:

The RabbitMQ connection parameters are set with environment variables, exchange and queue names are dependent on the
`service` value in `config.yaml` and the speaker name. The setup can be tested with the following sample
`docker-compose.yml` configuration:

```
version: '3'
services:
  rabbitmq:
    image: 'rabbitmq:3.6-alpine'
    environment:
      - RABBITMQ_DEFAULT_USER=${RABBITMQ_USER}
      - RABBITMQ_DEFAULT_PASS=${RABBITMQ_PASS}
  nmt_api:
    image: ghcr.io/tartunlp/translation-api:latest
    environment:
      - MQ_HOST=rabbitmq
      - MQ_PORT=5672
      - MQ_USERNAME=${RABBITMQ_USER}
      - MQ_PASSWORD=${RABBITMQ_PASS}
      - GUNICORN_WORKERS=8
    ports:
      - '5000:5000'
    depends_on:
      - rabbitmq
  nmt_worker_septilang:
    image: ghcr.io/tartunlp/translation-worker:latest
      - MODEL_NAME=septilang
      - MQ_HOST=rabbitmq
      - MQ_PORT=5672
      - MQ_USERNAME=${RABBITMQ_USER}
      - MQ_PASSWORD=${RABBITMQ_PASS}
    volumes:
      - ./models:/app/models
    depends_on:
      - rabbitmq
  nmt_worker_smugri:
    image: ghcr.io/tartunlp/translation-worker:latest
      - MODEL_NAME=smugri
      - MQ_HOST=rabbitmq
      - MQ_PORT=5672
      - MQ_USERNAME=${RABBITMQ_USER}
      - MQ_PASSWORD=${RABBITMQ_PASS}
    volumes:
      - ./models:/app/models
    depends_on:
      - rabbitmq
```