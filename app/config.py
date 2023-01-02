from typing import Optional, List, Dict

import yaml
from yaml.loader import SafeLoader
from pydantic import BaseSettings, BaseModel


class Workspace(BaseModel):
    name: str
    domains: List[str]


class Domain(BaseModel):
    name: str
    languages: List[str]


class APIConfig(BaseModel):
    api_keys: Dict[Optional[str], str]
    workspaces: Dict[str, Workspace]
    domains: Dict[str, Domain]
    language_codes: Dict[str, str]


class APISettings(BaseSettings):
    max_input_length: int = 10000
    config_path = "config/config.yaml"
    version: Optional[str] = None

    class Config:
        env_file = 'config/.env'
        env_prefix = 'api_'


class MQSettings(BaseSettings):
    host: str = 'localhost'
    port: int = 5672
    username: str = 'guest'
    password: str = 'guest'
    exchange: str = 'translation'
    connection_name: str = 'Translation API'
    timeout: int = 30

    class Config:
        env_file = 'config/.env'
        env_prefix = 'mq_'


api_settings = APISettings()
mq_settings = MQSettings()

with open(api_settings.config_path, 'r', encoding='utf-8') as f:
    api_config = APIConfig(**yaml.load(f, Loader=SafeLoader))
