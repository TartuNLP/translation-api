from os import environ
import json
import yaml
from yaml.loader import SafeLoader
from pika import ConnectionParameters, credentials
from dotenv import load_dotenv

load_dotenv("config/.env")
load_dotenv("config/sample.env")

CONFIG_FILE = 'config/config.yaml'

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    _config = yaml.load(f, Loader=SafeLoader)

SERVICE_NAME = _config['service']

WORKSPACES = {}
for name, workspace in _config['workspaces'].items():
    if workspace['info']:
        with open(workspace['info'], 'r') as file:
            info = json.load(file)
    else:
        info = {}
    for key in workspace['api_keys']:
        WORKSPACES[key] = {
            'name': name,
            'routing_pattern': workspace['routing_pattern'],
            'info': info
        }

MQ_PARAMETERS = ConnectionParameters(
    host=environ.get('MQ_HOST', 'localhost'),
    port=int(environ.get('MQ_PORT', '5672')),
    credentials=credentials.PlainCredentials(
        username=environ.get('MQ_USERNAME', 'guest'),
        password=environ.get('MQ_PASSWORD', 'guest')
    )
)

MESSAGE_TIMEOUT = int(environ.get('GUNICORN_TIMEOUT', '30')) * 1000
