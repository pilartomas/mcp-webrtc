# WebRTC Transport for Model Context Protocol

There are scenarios where neither **STDIO** nor **StreamableHTTP** transport can be used to connect an MCP client to an MCP server. **WebRTC** can often be used instead if there is some sort of signalling connection established between the two parties.

# Usage

```python
    from mcp_webrtc import webrtc_server_transport
    from aiortc.contrib.signaling import TcpSocketSignaling
    from mcp.server.lowlevel import Server
    from mcp.types import Tool

    app = Server("mcp-greeter")

    @app.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="greet",
                description="Greets the caller",
                inputSchema={
                    "type": "object",
                    "required": [],
                    "properties": {},
                },
            )
        ]

    async with webrtc_server_transport(TcpSocketSignaling("localhost", 8000)) as (read, write):
        await app.run(
            read, write, app.create_initialization_options()
        )
```

```python
    from mcp import ClientSession
    from mcp_webrtc import webrtc_client_transport
    from aiortc.contrib.signaling import TcpSocketSignaling

    async with (
        webrtc_client_transport(TcpSocketSignaling("localhost", 8000)) as (
            read,
            write,
        ),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        result = await session.list_tools()
        print(result.tools)
```
