import os

from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant. Be concise and stay respectful."
DEFAULT_SECRET_NAME = "api-key-ai"


class AzureChatClient:
    def __init__(
            self,
            *,
            endpoint: str,
            api_key: str,
            model: str,
    ) -> None:
        self._client = ChatCompletionsClient(
            endpoint=endpoint,  # Foundry endpoint (cognitiveservices.azure.com)
            credential=AzureKeyCredential(api_key),
        )
        self._model = model

    @classmethod
    def from_key_vault(
            cls,
            *,
            endpoint: str,
            model: str,
            vault_url: str,
            secret_name: str = DEFAULT_SECRET_NAME,
    ) -> "AzureChatClient":
        credential = DefaultAzureCredential()
        secret_client = SecretClient(vault_url=vault_url, credential=credential)
        api_key = secret_client.get_secret(secret_name).value

        return cls(
            endpoint=endpoint,
            api_key=api_key,
            model=model,
        )

    def get_chat_response(
            self,
            prompt: str,
            *,
            system_prompt: str = DEFAULT_SYSTEM_PROMPT,
            max_tokens: int = 1024,
    ) -> str:
        response = self._client.complete(
            model=self._model,  # e.g. "gpt-5.2-chat"
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""


def get_response(prompt: str) -> str:
    """
    Backwards-compatible alias for your main.py call: azure_module.get_response(message)
    """
    return get_chat_response(prompt)


def get_chat_response(
        prompt: str,
        *,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        max_tokens: int = 1024,
) -> str:
    """
    Module-level convenience wrapper that:
    - reads env vars
    - loads api key from Key Vault
    - calls Foundry model
    """
    endpoint = os.getenv("AZURE_AI_INFERENCE_ENDPOINT")
    model = os.getenv("AZURE_AI_MODEL")
    vault_url = os.getenv("AZURE_KEY_VAULT_URL")
    secret_name = os.getenv("AZURE_KEY_VAULT_SECRET_NAME", DEFAULT_SECRET_NAME)

    if not endpoint or not model or not vault_url:
        raise ValueError(
            "Missing configuration. Set AZURE_AI_INFERENCE_ENDPOINT, "
            "AZURE_AI_MODEL, and AZURE_KEY_VAULT_URL."
        )

    client = AzureChatClient.from_key_vault(
        endpoint=endpoint,
        model=model,
        vault_url=vault_url,
        secret_name=secret_name,
    )

    return client.get_chat_response(
        prompt,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
    )
