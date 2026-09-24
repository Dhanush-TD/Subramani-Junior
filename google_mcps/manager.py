from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from .auth import create_google_oauth_provider


class MCPManager:

    def __init__(self):
        self.sessions = {}
        self.transports = {}

    async def connect_calendar(self):

        if "calendar" in self.sessions:
            return self.sessions["calendar"]

        oauth_provider = create_google_oauth_provider()

        transport = streamablehttp_client(
            "https://calendarmcp.googleapis.com/mcp/v1",
            auth=oauth_provider,
        )

        streams = await transport.__aenter__()
        read_stream, write_stream, _ = streams

        session = ClientSession(
            read_stream,
            write_stream,
        )

        await session.__aenter__()

        await session.initialize()

        self.transports["calendar"] = transport
        self.sessions["calendar"] = session

        print("Google Calendar MCP connected.")

        return session

    async def get_calendar_tools(self):

        session = await self.connect_calendar()

        result = await session.list_tools()

        return result.tools

    async def close(self):

        for session in self.sessions.values():
            await session.__aexit__(None, None, None)

        for transport in self.transports.values():
            await transport.__aexit__(None, None, None)

        self.sessions.clear()
        self.transports.clear()