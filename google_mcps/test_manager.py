import asyncio

from .langchain_tools import GoogleMCPTools


async def main():

    google = GoogleMCPTools()

    tools = await google.get_calendar_tools()

    print("\nLangChain Calendar tools:\n")

    for tool in tools:
        print("-", tool.name)

    await google.close()


if __name__ == "__main__":
    asyncio.run(main())