from typing import Optional
import uuid, fcntl, time

from fastapi import APIRouter, Header, HTTPException, status, Depends

from app import mq_connector, mq_settings, api_config, Workspace
from . import Config, Request, Response, Domain, Correction

from datetime import datetime

v2_router = APIRouter(tags=["v2"])


def check_api_key(x_api_key: Optional[str] = Header(None, convert_underscores=True)) -> (Workspace, Optional[str]):
    try:
        workspace_name = api_config.api_keys[x_api_key]
        return api_config.workspaces[workspace_name], x_api_key
    except KeyError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect API key.")


@v2_router.get('/', include_in_schema=False)
@v2_router.get('', response_model=Config, description="Get the configuration of available NMT models.")
async def get_config(workspace_conf: tuple = Depends(check_api_key),):
    workspace, _ = workspace_conf
    return Config(
        domains=[Domain(
            name=api_config.domains[domain].name,
            code=domain,
            languages=api_config.domains[domain].languages
        ) for domain in workspace.domains]
    )


@v2_router.post('/', include_in_schema=False)
@v2_router.post('', response_model=Response, description="Submit a translation request.")
async def translate(body: Request,
                    workspace_conf: tuple = Depends(check_api_key),
                    application: Optional[str] = Header(None, convert_underscores=True, deprecated=True)):
    workspace, api_key = workspace_conf

    if body.domain not in workspace.domains:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Incorrect API key for domain '{body.domain}'.")

    if application and not body.application:
        body.application = application

    correlation_id = str(uuid.uuid4())
    routing_key = f"{mq_settings.exchange}.{body.src}.{body.tgt}.{body.domain}"

    result = await mq_connector.publish_request(correlation_id, body, routing_key)
    return result

@v2_router.post("/correction", description="Submit a translation correction request.")
async def correction(body: Correction, application: Optional[str] = Header(None, convert_underscores=True, deprecated=True)):
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    output = f"date: {dt_string}\n\nrequest: {body.request}\n\noriginalTranslation: {body.response}\n\ncorrectedTranslation: {body.correction}\n---\n\n"

    filePath= api_config.corrections_data_storage_path

    maxAttempts = 50
    attempt = 0
    while attempt < maxAttempts:
        try:
            with open(filePath, 'a') as f:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                f.write(output)
                return {"message": "Correction saved."}
        except IOError:
            attempt += 1
            # Failed to acquire lock, wait and try again
            time.sleep(.1)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save data on a server.")