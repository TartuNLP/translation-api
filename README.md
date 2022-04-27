# Machine Translation API

An API based on FastAPI for using TartuNLP's public NMT engines. The API is designed to be used together with our
[translation workers](https://github.com/TartuNLP/translation-worker).

The project is developed by the [NLP research group](https://tartunlp.ai) at the [Universty of Tartu](https://ut.ee).
Neural machine translation can also be tested in our [web demo](https://translate.ut.ee/).

The API is compatible with CAT tool plugins for [SDL Trados Studio](https://github.com/TartuNLP/SDL-Neurotolge-Plugin)
and [MemoQ](https://github.com/TartuNLP/MemoQ-Neurotolge-Plugin).

## API usage

The API can be used with the following request:

POST `/translation/v2`

HEADERS (optional):

```
x-api-key = public
```

BODY (json):

``` json
{
     "text": "Tere",
     "src": "et",
     "tgt": "en",
     "domain": "auto",
     "application": "test-application"
}
```

Response:

``` json
{
    "result": "Hi."
}
```

The full API documentation is available on the `/docs` endpoint path, for more info, check out the documentation
our [public API instance](https://api.tartunlp.ai/translation/docs).

## RabbitMQ communication

The API forwards requests to various NMT engines using the [RabbitMQ](https://rabbitmq.com) message broker. The
communication uses a direct exchange named `translation` and a routing key of the request parameters using the format
`translation.$src.$tgt.$domain`. To ensure compatibility with various CAT tools (and as many low-resource languages
don't have 2-letter codes), 3-letter ISO language codes are used. Note that by default, `ger` is used for German instead
on `deu`.

[NMT workers](https://github.com/TartuNLP/translation-worker)
estabilish queues within the exchange that are bound routing keys that illustrate which requests that the particular
model can handle. Therefore, infinite options are available for combining different models to handle requests within the
same API.

## Setup

The API can be deployed using the docker image published alongside the repository. Each image version correlates to a
specific release. The API is designed to work together with our
[translation worker](https://github.com/TartuNLP/translation-worker) worker containers and RabbitMQ.

The service is available on port `80`. By default, logging configuration is loaded from `config/logging.prod.ini` and
service configuration from `config/config.yaml` files. A default version of the latter is included with comments that
explain its format. To modify any config files, they should be mounted at `/app/config` (the absolute path in the
container).

The following environment variables should be specified when running the container:

- `MQ_USERNAME` - RabbitMQ username
- `MQ_PASSWORD` - RabbitMQ user password
- `MQ_HOST` - RabbitMQ host
- `MQ_PORT` (optional) - RabbitMQ port (`5672` by default)
- `MQ_TIMEOUT` (optional) - Message timeout in milliseconds (`300000` by default)
- `MQ_EXCHANGE` (optional) - RabbitMQ exchange name (`translation` by default)
- `MQ_CONNECTION_NAME` (optional) - friendly connection name (`Translation API` by default)
- `API_MAX_INPUT_LENGTH` (optional) - maximum input text length in characters (`10000` by default)
- `API_CONFIG_PATH` (optional) - path of the config file used (`config/config.yaml`)

The entrypoint of the container is `["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers"]`.

The default `CMD` is used to define logging configuration `["--log-config", "config/logging.prod.ini"]` which can be
potentially overridden to define different [Uvicorn parameters](https://www.uvicorn.org/deployment/). For example,
`["--log-config", "config/logging.debug.ini", "--root-path", "/translation"]` enables debug logging and allows the API
to be mounted under to the non-root path `/translation` when using a proxy server such as Nginx.

The setup can be tested with the following sample `docker-compose.yml` configuration:

``` yaml
version: '3'
services:
  rabbitmq:
    image: 'rabbitmq'
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
    ports:
      - '80:80'
    depends_on:
      - rabbitmq
  nmt_worker:
    image: ghcr.io/tartunlp/translation-worker:latest
      - MQ_HOST=rabbitmq
      - MQ_PORT=5672
      - MQ_USERNAME=${RABBITMQ_USER}
      - MQ_PASSWORD=${RABBITMQ_PASS}
      - MKL_NUM_THREADS=8
    volumes:
      - ./models:/app/models
    command: ["--model-name", "septilang"]
    depends_on:
      - rabbitmq
```

### Development setup

The API uses Python 3.10 by default, but is likely to be compatible with earlier versions. All required packages are
described in `requirements.txt`, to install them, use:

``` bash
pip install --no-cache-dir --upgrade --user -r requirements.txt
```

Environment variables described in the selection above can be defined in `config/.env`. The file is ignored by Git and
Docker.

To run the API, use the following command. This will start the service on `localhost` port `8000` and automatically
restart the server in case of any code changes.

``` bash
uvicorn app:app --reload
```