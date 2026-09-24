from langchain_mcp_adapters.client import MultiServerMCPClient


async def get_mcp_tools():

    client = MultiServerMCPClient(
        {
            # MCP servers will be added here
        }
    )

    tools = await client.get_tools()

    return tools