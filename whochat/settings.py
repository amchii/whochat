from pathlib import Path

from pydantic import BaseSettings


class Settings(BaseSettings):
    DEBUG: bool = False
    ROOT_DIR = Path(__file__).parent.parent.absolute()
    DEV_LOG_DIR = ROOT_DIR.joinpath("logs")
    DEFAULT_LOG_LEVEL = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
