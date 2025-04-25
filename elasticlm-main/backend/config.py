from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load the .env file
env_path = Path(__file__).resolve().parent / ".env"  # Adjust the path if .env is located elsewhere
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    ES_URL: str = "http://localhost:9200"
    ES_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    OTEL_ENABLED: bool = False

    # **Added Fields**
    AZURE_OPENAI_API_VERSION: str
    AZURE_OPENAI_DEPLOYMENT_NAME: str
    LANGSMITH_PROJECT: str = ""

    SECRET_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

DEFAULT_INDEX = "elastic_lm_docs"
settings = Settings()

# ===== LLM Prompts and Schemas =====

PLANNER_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "plan_schema",
        "schema": {
            "type": "object",
            "properties": {
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string"},
                            "args": {"type": "object"},
                            "description": {"type": "string"}
                        },
                        "required": ["action", "args"]
                    }
                }
            },
            "required": ["steps"],
            "additionalProperties": False
        }
    }
}