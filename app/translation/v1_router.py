from typing import Optional
import uuid

from fastapi import APIRouter, HTTPException, status, Depends, Query

from app import mq_connector, mq_settings, api_config, Workspace
from . import ConfigV1, RequestV1, ResponseV1, DomainV1, Response, Request

v1_router = APIRouter(tags=["v1"])


def check_v1_api_key(
        auth: Optional[str] = Query(
            None,
            description="An optional API key parameter that determines which domains and langauge pairs are available"
        )) -> Workspace:
    try:
        workspace_name = api_config.api_keys[auth]
        return api_config.workspaces[workspace_name]
    except KeyError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect API key.")


@v1_router.get('/', include_in_schema=False)
@v1_router.get('/support', include_in_schema=False)
@v1_router.get('', response_model=ConfigV1, description="Get the configuration of available NMT models.")
async def get_config_v1(workspace: Workspace = Depends(check_v1_api_key)):
    return ConfigV1(
        domain=workspace.name,
        options=[DomainV1(
            odomain=domain,
            name=api_config.domains[domain].name,
            lang=list(set([lang_pair.split('-')[1] for lang_pair in api_config.domains[domain].languages]))
        ) for domain in workspace.domains]
    )


@v1_router.post('/', include_in_schema=False)
@v1_router.post('', response_model=ResponseV1, description="Submit a translation request.")
async def translate(body: RequestV1,
                    ilang: Optional[str] = Query(default=None,
                                                 description="Source language ISO 2-letter or 3-letter code."),
                    olang: str = Query(default=None, description="Target language ISO 2-letter or 3-letter code."),
                    odomain: Optional[str] = Query(default="general", description="The domain (style) of the text"),
                    workspace: Workspace = Depends(check_v1_api_key)):
    if odomain not in workspace.domains:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Incorrect auth key for domain '{odomain}'.")

    try:
        tgt = api_config.language_codes[olang]
    except KeyError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Unsupported output language {olang}'.")

    src = False
    if ilang is None:
        for language_pair in api_config.domains[odomain].languages:
            if language_pair.split('-')[1] == tgt:
                src = language_pair.split('-')[0]
    else:
        try:
            src = api_config.language_codes[ilang]
        except KeyError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"Unsupported input language {ilang}'.")

    if not src:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Incorrect output language {olang} for domain '{odomain}'.")
    elif f"{src}-{tgt}" not in api_config.domains[odomain].languages:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Incorrect language pair {src}-{tgt} for domain '{odomain}'.")

    correlation_id = str(uuid.uuid4())
    routing_key = f"{mq_settings.exchange}.{src}.{tgt}.{odomain}"

    request = Request(
        text=body.text,
        src=src,
        tgt=tgt,
        domain=odomain,
        application="memoq"  # input type with best support for all tag types
    )

    result = await mq_connector.publish_request(correlation_id, request, routing_key)
    result = Response(**result)
    v1_result = ResponseV1(
        input=request.text,
        result=result.result
    )
    return v1_result
