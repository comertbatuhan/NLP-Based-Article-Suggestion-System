# data/config.py
from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Central config for OpenAlex client.

    You can override any field via env vars with OPENALEX_ prefix, e.g.:
      OPENALEX_MAILTO="[email protected]"
      OPENALEX_PER_PAGE="200"
    """
    base_url: AnyHttpUrl = "https://api.openalex.org"
    timeout_s: int = 20
    per_page: int = Field(20, ge=1, le=200)  # OpenAlex allows max 200 per page
    max_retries: int = 3                      # network + 429/5xx retries
    backoff_factor: float = 0.8               # exponential backoff base


settings = Settings()
