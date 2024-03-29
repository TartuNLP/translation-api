from typing import List, Union, Any

from pydantic import BaseModel, Field
from fastapi import HTTPException, status

from app import api_settings


class RequestV1(BaseModel):
    text: Union[str, List[str]] = Field(...,
                                        description="Original text input. May contain multiple sentences.",
                                        example="Aitäh!")

    def __init__(self, **data: Any):
        super().__init__(**data)

        length = len(self.text) if type(self.text) == str else sum([len(sent) for sent in self.text])
        if length > api_settings.max_input_length:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Field 'text' must not contain more than {api_settings.max_input_length} characters.")


class ResponseV1(BaseModel):
    status: str = Field("done",
                        description="A status code of the request",
                        example="done")
    input: Union[str, List[str]] = Field(...,
                                         description="Original text input.",
                                         example="Aitäh!")
    result: Union[str, List[str]] = Field(...,
                                          description="Translated text.",
                                          example="Thank you!")


class DomainV1(BaseModel):
    odomain: str = Field(...,
                         example="general",
                         description="A machine-readable codaname of the domain")
    name: str = Field(...,
                      example="General",
                      description="A human-readable name of the domain")
    lang: List[str] = Field(...,
                            example=["est", "eng"],
                            description="A list of allowed output languages.")


class ConfigV1(BaseModel):
    domain: str = Field(...,
                        description="Name of the workspace of the auth key used.")
    options: List[DomainV1] = Field(...,
                                    description="A list of supported domains and their configurations.")
