from __future__ import annotations

import os
import logging
from typing import Optional

from openai import AzureOpenAI

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

logger = logging.getLogger("app.ai_communication")
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------

DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant. Be concise and stay respectful."
DEFAULT_API_VERSION = "2024-12-01-preview"
DEFAULT_SECRET_NAME = "api-key-ai"

# ---------------------------------------------------------------------
# Settings loading
# ---------------------------------------------------------------------

def _load_api_key() -> str:
    """
    Load API key either directly from env or via Key Vault (Managed Identity).
    """

    # 1️⃣ Direct API key (preferred & simplest)
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if api_key:
        logger.info("Using AZURE_OPENAI_API_KEY from environment")
        return api_key

    # 2️⃣ Key Vault fallback
    vault_url = os.getenv("AZURE_KEY_VAULT_URL")
    if not vault_url:
        raise ValueError(
            "Missing API key. Set AZURE_OPENAI_API_KEY or AZURE_KEY_VAULT_URL."
        )

    secret_name = os.getenv("AZURE_KEY_VAULT_SECRET_NAME", DEFAULT_SECRET_NAME)

    logger.info("Fetching API key from Key Vault | vault=%s | secret=%s", vault_url, secret_name)

    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=vault_url, credential=credential)

    return secret_client.get_secret(secret_name).value


def _load_settings() -> tuple[str, str, str]:
    """
    Returns (endpoint, deployment, api_version)
    """

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", DEFAULT_API_VERSION)

    if not endpoint:
        raise ValueError("Missing AZURE_OPENAI_ENDPOINT")
    if not deployment:
        raise ValueError("Missing AZURE_OPENAI_DEPLOYMENT")

    logger.info("Azure OpenAI configuration")
    logger.info("  Endpoint: %s", endpoint)
    logger.info("  Deployment: %s", deployment)
    logger.info("  API Version: %s", api_version)

    return endpoint, deployment, api_version


# ---------------------------------------------------------------------
# Client wrapper
# ---------------------------------------------------------------------

class AzureChatClient:
    def __init__(self) -> None:
        endpoint, deployment, api_version = _load_settings()
        api_key = _load_api_key()

        self._deployment = deployment

        self._client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )

        logger.info("AzureOpenAI client initialized successfully")

    def get_chat_response(
            self,
            prompt: str,
            *,
            system_prompt: str = DEFAULT_SYSTEM_PROMPT,
            max_tokens: int = 1024,
    ) -> str:

        response = self._client.chat.completions.create(
            model=self._deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=max_tokens,
        )

        return response.choices[0].message.content or ""


# ---------------------------------------------------------------------
# Public API used by FastAPI
# ---------------------------------------------------------------------

_client: Optional[AzureChatClient] = None


def get_response(prompt: str) -> str:
    """
    Entry point used by FastAPI.
    """

    logger.info("get_response called | prompt_length=%d", len(prompt) if prompt else 0)

    global _client
    if _client is None:
        _client = AzureChatClient()

    try:
        response = _client.get_chat_response(prompt)

        logger.info(
            "get_response success | response_length=%d",
            len(response) if response else 0,
        )

        return response

    except Exception as exc:
        logger.exception(
            "get_response failed | error_type=%s | error_message=%s",
            type(exc).__name__,
            str(exc),
        )
        raise
