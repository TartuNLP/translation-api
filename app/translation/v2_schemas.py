from typing import List, Union, Optional, Any

from pydantic import BaseModel, Field, validator
from fastapi import HTTPException, status

from app import api_settings, api_config


class Request(BaseModel):
    text: Union[str, List[str]] = Field(...,
                                        description="Original text input. May contain multiple sentences.",
                                        example="Aitäh!")
    src: str = Field(...,
                     example="est",
                     description="Input language ISO 2-letter or 3-letter code.")
    tgt: str = Field(...,
                     example="eng",
                     description="Target language ISO 2-letter or 3-letter code.")
    domain: str = Field("general",
                        example="general",
                        description="The domain (style) of the text. This is mostly relevant for custom-made engines.")
    application: Optional[str] = Field(None,
                                       example="Documentation UI",
                                       description="Name of the application making the request. Certain application "
                                                   "names may activate specific pre- and postprocessing pipelines. "
                                                   "Otherwise used for usage statistics. If you integrate our API into "
                                                   "your application, please use a consistent application name and let "
                                                   "us know.")

    def __init__(self, **data: Any):
        super(Request, self).__init__(**data)

    @validator('text')
    def check_input_length(cls, v):
        length = len(v) if type(v) == str else sum([len(sent) for sent in v])
        if length > api_settings.max_input_length:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Field 'text' must not contain more than {api_settings.max_input_length} characters.")
        return v

    @validator('src', 'tgt')
    def check_languages(cls, v):
        if v not in api_config.language_codes.keys():
            raise ValueError(f"Unknown language '{v}'.")
        return api_config.language_codes[v]

    @validator('domain')
    def check_domain(cls, v, values):
        if v not in api_config.domains.keys():
            raise ValueError(f"Domain '{v}' not available.")
        language_pair = f"{values['src']}-{values['tgt']}"
        if language_pair not in api_config.domains[v].languages:
            raise ValueError(f"Language pair '{language_pair}' not available for domain '{v}'.")
        return v


class Response(BaseModel):
    result: Union[str, List[str]] = Field(...,
                                          description="Translated text.",
                                          example="Thank you!")


class Domain(BaseModel):
    name: str = Field(...,
                      example="General",
                      description="A human-readable name of the domain")
    code: str = Field(...,
                      example="general",
                      description="A machine-readable codaname of the domain")
    languages: List[str] = Field(...,
                                 example=["est-eng", "eng-est"],
                                 description="A list of supported language pairs. Each pair is given as a hyphen-"
                                             "separated string of the source and target language 3-letter ISO codes. "
                                             "Note that for German 'ger' is used instead of 'deu'.")


class Config(BaseModel):
    xml_support: bool = Field(True,
                              description="[Deprecated] A boolean value whether using XML tags in text is supported.")
    domains: List[Domain] = Field(...,
                                  description="A list of supported domains and their configurations.")
