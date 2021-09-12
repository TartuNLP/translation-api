import logging
from flask_cors import CORS
from nauron import Nauron
from flask import abort

import settings
from utils import V2_BODY, V2_HEADERS, parser, resolve_workspace

logger = logging.getLogger("gunicorn.error")

app = Nauron(__name__, timeout=settings.MESSAGE_TIMEOUT, mq_parameters=settings.MQ_PARAMETERS)
CORS(app)

nmt = app.add_service(name=settings.SERVICE_NAME, remote=True)


@app.post('/translation/v2')
@parser.use_args(V2_HEADERS, location="headers")
@parser.use_args(V2_BODY, location="json")
def translate(headers, body):
    workspace = resolve_workspace(headers.pop("x-api-key"))
    content = {**headers, **body}

    routing_key = workspace['name']
    for key in workspace['routing_pattern']:
        try:
            routing_key += '.{}'.format(content[key])
        except KeyError:
            abort(400, description='Mandatory parameter {} missing'.format(key))

    response = nmt.process_request(content=content, routing_key=routing_key)
    return response


@app.get('/translation/v2')
@parser.use_args(V2_HEADERS, location="headers")
def config(headers):
    """
    Returns machine-readable workspace configuration for CAT tools.
    """
    workspace = resolve_workspace(headers["x-api-key"])
    response = workspace["info"]
    return response


if __name__ == '__main__':
    app.run()
