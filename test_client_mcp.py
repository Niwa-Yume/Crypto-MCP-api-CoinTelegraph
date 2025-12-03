import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp():
    server_params = StdioServerParameters(
        command="python",
        args=["MCP.py"]  #chemin a ajusté si c'est pas au meme niveau d'arboresence
    )

    async with stdio_client(server_params) as (read, write): #lance le mcp.py en arrière plan
        async with ClientSession(read, write) as session:
            await session.initialize() #co avec le mcp

            # session ini
            result = await session.call_tool("lire_classement_crypto", {"limit": 3})
            print(result)


if __name__ == "__main__":
    asyncio.run(test_mcp())
