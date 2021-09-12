# Machine Translation API

A Flask API for using TartuNLP's public NMT engines. The API is designed to be used together with our 
[translation workers](https://github.com/TartuNLP/translation-worker).

The project is developed by the [NLP research group](https://tartunlp.ai) at the [Universty of Tartu](https://ut.ee).
Neural machine translation can also be tested in our [web demo](https://translate.ut.ee/).

## API usage

To use the API, use the following POST request format:

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

In case the text field contains a string, it is automatically split into sentences, which are translated and merged into
a single string. In case it contains a list, the service assumes this list to be a list of sentences and will not do any
further splitting.

The `olang` and `odomain` parameters are for the output language and output domain. The `auth` field is used to 
decide which engine is used. A list of possible configurations for each `auth` token can be seen with a GET request 
at the same endpoint. 

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