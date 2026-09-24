import asyncio
import os
from dotenv import load_dotenv

from browser_use import Agent
from browser_use.llm import ChatOpenAI

load_dotenv()


async def main():
    llm = ChatOpenAI(
        model="z-ai/glm-5.2",
        api_key=os.getenv("NVIDIA_API_KEY"),
        base_url="https://integrate.api.nvidia.com/v1",
    )

    agent = Agent(
        task="Open Google and search for Python",
        llm=llm,
    )

    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())