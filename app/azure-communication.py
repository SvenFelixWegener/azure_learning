import os

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from openai import AzureOpenAI

DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant. Be concise and stay respectful."
DEFAULT_API_VERSION = "2024-12-01-preview"
DEFAULT_SECRET_NAME = "api-key-value"
AZURE_ENDPOINT ="https://info-mko5tqe9-swedencentral.cognitiveservices.azure.com/"



class AzureChatClient:
    def __init__(
            self,
            *,
            endpoint: str,
            api_key: str,
            deployment: str,
            api_version: str = DEFAULT_API_VERSION,
    ) -> None:
        self._client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=AZURE_ENDPOINT,
            api_key=api_key,
        )
        self._deployment = deployment

    @classmethod
    def from_key_vault(
            cls,
            *,
            endpoint: str,
            deployment: str,
            vault_url: str,
            secret_name: str = DEFAULT_SECRET_NAME,
            api_version: str = DEFAULT_API_VERSION,
    ) -> "AzureChatClient":
        credential = DefaultAzureCredential()
        secret_client = SecretClient(vault_url=vault_url, credential=credential)
        api_key = secret_client.get_secret(secret_name).value
        return cls(
            endpoint=endpoint,
            api_key=api_key,
            deployment=deployment,
            api_version=api_version,
        )

    def get_chat_response(
            self,
            prompt: str,
            *,
            system_prompt: str = DEFAULT_SYSTEM_PROMPT,
            max_tokens: int = 1024,
    ) -> str:
        response = self._client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=max_tokens,
            model=self._deployment,
        )
        return response.choices[0].message.content or ""


def get_chat_response(
        prompt: str,
        *,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        max_tokens: int = 1024,
) -> str:
    endpoint = AZURE_ENDPOINT
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    vault_url = os.getenv("AZURE_KEY_VAULT_URL")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", DEFAULT_API_VERSION)

    if not endpoint or not deployment or not vault_url:
        raise ValueError(
            "Missing configuration. Set AZURE_OPENAI_ENDPOINT, "
            "AZURE_OPENAI_DEPLOYMENT, and AZURE_KEY_VAULT_URL."
        )

    client = AzureChatClient.from_key_vault(
        endpoint=endpoint,
        deployment=deployment,
        vault_url=vault_url,
        api_version=api_version,
    )
    return client.get_chat_response(
        prompt,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
    )