from langchain_mcp_adapters.tools import load_mcp_tools

from .manager import MCPManager


class GoogleMCPTools:

    def __init__(self):
        self.manager = MCPManager()

    async def get_calendar_tools(self):
        session = await self.manager.connect_calendar()

        tools = await load_mcp_tools(
            session,
        )

        return tools

    async def close(self):
        await self.manager.close()