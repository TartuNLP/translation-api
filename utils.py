from flask import abort
from webargs import fields
from webargs.flaskparser import FlaskParser
from nauron import Response

import settings

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
