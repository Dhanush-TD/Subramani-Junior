
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
        reasoning_effort="high",
    )

    task = """Research whether PostgreSQL or MongoDB is the better database choice for a new AI-powered application in 2026. Visit the official documentation for both and at least 3 independent reputable sources. Compare performance, scalability, data modeling, vector search/AI capabilities, transactions, ecosystem, hosting options, and cost. Give a recommendation for a small development team building an AI application, with sources. Do not rely on a single website."""

    agent = Agent(
        task=task,
        llm=llm,
    )

    result = await agent.run()

    print("\n" + "=" * 80)
    print("FINAL RESULT")
    print("=" * 80)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())

