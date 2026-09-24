import asyncio
import os
from dotenv import load_dotenv

from browser_use import Agent
from browser_use.llm import ChatOpenAI

load_dotenv()

async def main():
    llm = ChatOpenAI(
        model="gpt-5.6-luna",
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    agent = Agent(
        
        llm=llm,
    )

    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())