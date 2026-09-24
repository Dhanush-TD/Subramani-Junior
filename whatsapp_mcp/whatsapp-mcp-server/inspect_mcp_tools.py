import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.list_tools()

            for tool in result.tools:
                print("\n" + "=" * 70)
                print(f"TOOL: {tool.name}")
                print("=" * 70)
                print("DESCRIPTION:")
                print(tool.description or "No description")
                print("\nINPUT SCHEMA:")
                print(json.dumps(tool.inputSchema, indent=2))


asyncio.run(main())
