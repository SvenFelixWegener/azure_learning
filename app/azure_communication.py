"""
Azure AI Foundry / Azure AI Inference integration.

This module is meant to be imported normally from within the same package, e.g.:
    from . import azure_communication

It supports two common ways to provide the model API key:
1) Directly via environment variable AZURE_AI_API_KEY (recommended for App Service if you
   don't have Managed Identity + Key Vault permissions configured yet).
2) Via Azure Key Vault (AZURE_KEY_VAULT_URL + secret name), using DefaultAzureCredential.

For Azure AI Model Inference (Foundry Models), the endpoint typically looks like:
  https://<resource-name>.<region>.services.ai.azure.com
or sometimes a project/managed endpoint.

The azure-ai-inference SDK expects the *inference base* endpoint; in practice, the safest
is to provide the endpoint ending in /models (we normalize it below).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from azure.core.credentials import AzureKeyCredential
from azure.ai.inference import ChatCompletionsClient

# Only needed if you use Key Vault:
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant. Be concise and stay respectful."
DEFAULT_SECRET_NAME = "api-key-ai"

@dataclass(frozen=True)
class Settings:
    endpoint: str
    model: str
    api_key: str
    api_version: Optional[str] = None  # forwarded to the SDK (if supported)


def _load_settings() -> Settings:
    endpoint = os.getenv("AZURE_AI_INFERENCE_ENDPOINT") or os.getenv("AZURE_OPENAI_ENDPOINT")
    model = os.getenv("AZURE_AI_MODEL") or os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.getenv("AZURE_AI_INFERENCE_API_VERSION") or os.getenv("AZURE_OPENAI_API_VERSION")

    if not endpoint:
        raise ValueError(
            "Missing configuration: set AZURE_AI_INFERENCE_ENDPOINT (recommended) "
            "or AZURE_OPENAI_ENDPOINT."
        )
    if not model:
        raise ValueError(
            "Missing configuration: set AZURE_AI_MODEL (recommended) "
            "or AZURE_OPENAI_DEPLOYMENT."
        )

    # Preferred: direct API key
    api_key = os.getenv("AZURE_AI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    if api_key:
        return Settings(
            endpoint=endpoint,
            model=model,
            api_key=api_key,
            api_version=api_version,
        )

    # Fallback: Key Vault
    vault_url = os.getenv("AZURE_KEY_VAULT_URL")
    secret_name = os.getenv("AZURE_KEY_VAULT_SECRET_NAME", DEFAULT_SECRET_NAME)
    if not vault_url:
        raise ValueError(
            "Missing API key. Set AZURE_AI_API_KEY (recommended) "
            "or configure Key Vault by setting AZURE_KEY_VAULT_URL "
            f"(and optionally AZURE_KEY_VAULT_SECRET_NAME, default '{DEFAULT_SECRET_NAME}')."
        )

    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=vault_url, credential=credential)
    api_key = secret_client.get_secret(secret_name).value

    logger.info("Initializing AzureChatClient")
    logger.info("  Endpoint: %s", endpoint)
    logger.info("  Model: %s", model)
    logger.info("  API Version: %s", api_version)

    return Settings(
        endpoint=endpoint,
        model=model,
        api_key=api_key,
        api_version=api_version,
    )


class AzureChatClient:
    """Thin wrapper around azure-ai-inference ChatCompletionsClient."""

    def __init__(self, *, endpoint: str, api_key: str, model: str, api_version: Optional[str] = None) -> None:
        endpoint = endpoint
        kwargs = {}
        # azure-ai-inference supports passing client keywords (docs mention api_version)
        if api_version:
            kwargs["api_version"] = api_version

        self._client = ChatCompletionsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key),
            **kwargs,
        )
        self._model = model

    def get_chat_response(
            self,
            prompt: str,
            *,
            system_prompt: str = DEFAULT_SYSTEM_PROMPT,
            max_tokens: int = 1024,
    ) -> str:
        response = self._client.complete(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""


# ---- Public helper used by FastAPI ----

_client: Optional[AzureChatClient] = None


def get_response(prompt: str) -> str:
    logger.info(
        "get_response called | prompt_length=%d",
        len(prompt) if prompt else 0
    )

    global _client
    if _client is None:
        s = _load_settings()
        _client = AzureChatClient(
            endpoint=s.endpoint,
            api_key=s.api_key,
            model=s.model,
            api_version=s.api_version,
        )

    try:
        response = _client.get_chat_response(prompt)

        logger.info(
            "get_response success | response_length=%d",
            len(response) if response else 0
        )

        return response

    except Exception as exc:
        logger.exception(
            "get_response failed | error_type=%s | error_message=%s",
            type(exc).__name__,
            str(exc),
        )
        raise
