import os
from openai import AzureOpenAI

client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint="https://info-mko5tqe9-swedencentral.cognitiveservices.azure.com/",
    api_key="secret",

)

model_name = "gpt-5.2-chat"
deployment = "gpt-5.2-chat"

response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a not so helpful assistant, you behave like a drunken uncle on christmas. Exagerate but stay political correct",
        },
        {
            "role": "user",
            "content": "I have a fox, a chicken, and a bag of grain that I need to take over a river in a boat. I can only take one thing at a time. If I leave the chicken and the grain unattended, the chicken will eat the grain. If I leave the fox and the chicken unattended, the fox will eat the chicken. How can I get all three things across the river without anything being eaten? Explain your reasoning.",
        }
    ],
    max_completion_tokens =16384,
    model=deployment
)

print(response.choices[0].message.content)



