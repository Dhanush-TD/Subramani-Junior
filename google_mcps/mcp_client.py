from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from .auth import create_google_oauth_provider


CALENDAR_MCP_URL = "https://calendarmcp.googleapis.com/mcp/v1"


async def get_calendar_tools():

    oauth_provider = create_google_oauth_provider()

    transport = streamablehttp_client(
        CALENDAR_MCP_URL,
        auth=oauth_provider,
    )

    read_stream, write_stream, _ = await transport.__aenter__()

    session = ClientSession(
        read_stream,
        write_stream,
    )

    await session.__aenter__()

    await session.initialize()

    result = await session.list_tools()

    return session, transport, result.tools