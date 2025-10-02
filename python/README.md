# WebRTC Transport for Model Context Protocol

[The Model Context Protocol (MCP)](https://modelcontextprotocol.io) is an open standard for connecting AI applications to external systems, such as tools and data sources. It defines several transport mechanisms for client-server communication, including STDIO (over standard input/output) and Streamable HTTP (for web-based streaming).

However, there are scenarios—such as in browser environments or firewalled networks—where neither STDIO nor Streamable HTTP can effectively connect an MCP client to an MCP server. In these cases, [WebRTC](https://webrtc.org/) provides a peer-to-peer alternative, leveraging real-time communication capabilities, provided a signaling connection (e.g., via WebSockets or another channel) is established between the parties.

This repository implements a WebRTC-based transport layer compatible with the MCP specification, enabling seamless integration in constrained networking setups.

## Installation

```bash
pip install mcp-webrtc
```

## Usage

### Server

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

### Client

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
