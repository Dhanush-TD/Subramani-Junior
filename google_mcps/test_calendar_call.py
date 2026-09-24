import asyncio

from google_mcps.langchain_tools import GoogleMCPTools


async def main():
    google = GoogleMCPTools()

    try:
        tools = await google.get_calendar_tools()

        print("\nCalling list_calendars...\n")

        tool = next(
            t for t in tools
            if t.name == "list_calendars"
        )

        result = await tool.ainvoke({})

        print("RESULT:")
        print(result)

    finally:
        await google.close()


if __name__ == "__main__":
    asyncio.run(main())