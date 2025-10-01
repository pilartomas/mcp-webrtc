# WebRTC Transport for Model Context Protocol

There are scenarios where neither **STDIO** nor **StreamableHTTP** transport can be used to connect an MCP client to an MCP server. **WebRTC** can often be used instead if there is some sort of signalling connection established between the two parties.

# Usage

```python
    from mcp_webrtc import webrtc_server_transport
    from aiortc.contrib.signaling import CopyPasteSignaling

    async with webrtc_server_transport(CopyPasteSignaling()) as (read, write):
        app.run(
            read, write, app.create_initialization_options()
        )
```

```python
    from mcp import ClientSession
    from mcp_webrtc import webrtc_client_transport
    from aiortc.contrib.signaling import CopyPasteSignaling

    async with (
        webrtc_client_transport(client_signaling) as (
            read,
            write,
        ),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        result = await session.list_tools()
        print(result.tools)
```
