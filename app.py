import logging
from flask_cors import CORS
from nauron import Nauron
from flask import abort

import settings
from utils import QUERY, BODY, parser, resolve_workspace

logger = logging.getLogger("gunicorn.error")

app = Nauron(__name__, timeout=settings.MESSAGE_TIMEOUT, mq_parameters=settings.MQ_PARAMETERS)
app.secret_key = settings.SECRET_KEY
CORS(app)

nmt = app.add_service(name=settings.SERVICE_NAME, remote=True)


@app.get('/translation/v1')
@parser.use_args(QUERY, location="query")
def config_v1(query):
    workspace = resolve_workspace(query.pop("auth"))
    return workspace['info']


@app.post('/translation/v1')
@parser.use_args(QUERY, location="query")
@parser.use_args(BODY, location="json")
def translate_v1(query, body):
    workspace = resolve_workspace(query.pop("auth"))

    content = body
    if 'olang' in query:
        content['tgt'] = query['olang']
    if 'odomain' in query:
        content['domain'] = query['odomain']

    routing_key = workspace['name']
    for key in workspace['routing_pattern']:
        try:
            routing_key += '.{}'.format(content[key])
        except KeyError:
            abort(400, description='Mandatory parameter {} missing'.format(key))

    return nmt.process_request(content=content, routing_key=routing_key)


if __name__ == '__main__':
    app.run()
