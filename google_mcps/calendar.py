import asyncio

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from .auth import create_google_oauth_provider


CALENDAR_MCP_URL = "https://calendarmcp.googleapis.com/mcp/v1"


async def main():
    oauth_provider = create_google_oauth_provider()

    print("Connecting to Google Calendar MCP...")

    async with streamablehttp_client(
        CALENDAR_MCP_URL,
        auth=oauth_provider,
    ) as (read_stream, write_stream, _):

        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            print("Initializing MCP session...")

            await session.initialize()

            print("\nConnected to Google Calendar MCP!")

            result = await session.list_tools()

            print("\nAvailable Calendar tools:\n")

            for tool in result.tools:
                print(f"- {tool.name}")


if __name__ == "__main__":
    asyncio.run(main())