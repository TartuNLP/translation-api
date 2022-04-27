import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app import mq_connector
from app.translation import v1_router, v2_router

logger = logging.getLogger(__name__)

app = FastAPI(title="Translation API",
              version="2.1.0",
              description="An API that provides translations using neural machine translation models. "
                          "Developed by TartuNLP - the NLP research group of the University of Tartu.",
              terms_of_service="https://www.tartunlp.ai/andmekaitsetingimused",
              license_info={
                  "name": "MIT license",
                  "url": "https://github.com/TartuNLP/translation-api/blob/main/LICENSE"
              },
              contact={
                  "name": "TartuNLP",
                  "url": "https://tartunlp.ai",
                  "email": "ping@tartunlp.ai",
              })

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
    logger.debug(f"{request}: {exc_str}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"message": exc_str}
    )


@app.on_event("startup")
async def startup():
    await mq_connector.connect()


@app.on_event("shutdown")
async def shutdown():
    await mq_connector.disconnect()


app.include_router(v2_router, prefix="/v2")
app.include_router(v1_router, prefix="/v1", deprecated=True)
