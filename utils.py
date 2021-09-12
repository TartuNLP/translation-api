from flask import abort
from webargs import fields
from webargs.flaskparser import FlaskParser
from nauron import Response

import settings

V1_QUERY = {
    'auth': fields.Str(required=True),
    'olang': fields.Str(),
    'odomain': fields.Str()
}

V1_BODY = {
    'text': fields.Raw(required=True, validate=(lambda obj: type(obj) in [str, list]))
}

V2_HEADERS = {
    "x-api-key": fields.Str(missing="public"),
    "application": fields.Str()
}

V2_BODY = {
    'text': fields.Raw(required=True, validate=(lambda obj: type(obj) in [str, list])),
    'src': fields.Str(),
    'tgt': fields.Str(),
    'domain': fields.Str(),
    "application": fields.Str()
}


def config_converter(name: str, config: dict) -> dict:
    """
    Convert v2 config to v1 format
    """
    v1_config = {
        'domain': name,
        'options': []
    }
    for domain in config['domains']:
        option = {
            'odomain': domain['name'],
            'name': domain['code'],
            'lang': []
        }
        languages = []
        for lang_pair in domain['languages']:
            languages.append(lang_pair.split('-')[1])
        option['languages'] = list(set(languages))
        v1_config['options'].append(option)

    return v1_config


parser = FlaskParser()


@parser.error_handler
def _handle_error(error, *_, **__):
    Response(content=error.messages, http_status_code=400).flask_response()


def resolve_workspace(key):
    """
    Resolves the workspace configuration based on the api key in request header.
    """
    try:
        return settings.WORKSPACES[key]
    except KeyError:
        abort(401, description="Invalid authentication token.")
