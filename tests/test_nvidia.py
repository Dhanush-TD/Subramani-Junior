import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


load_dotenv()


llm = ChatOpenAI(

    base_url="https://integrate.api.nvidia.com/v1",

    api_key=os.getenv(
        "NVIDIA_API_KEY"
    ),

    model="z-ai/glm-5.2",
)


response = llm.invoke(
    "Say hello"
)


print(response.content)