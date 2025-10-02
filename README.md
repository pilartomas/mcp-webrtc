# WebRTC Transport for Model Context Protocol

[The Model Context Protocol (MCP)](https://modelcontextprotocol.io) is an open standard for connecting AI applications to external systems, such as tools and data sources. It defines several transport mechanisms for client-server communication, including STDIO (over standard input/output) and Streamable HTTP (for web-based streaming).

However, there are scenarios—such as in browser environments or firewalled networks—where neither STDIO nor Streamable HTTP can effectively connect an MCP client to an MCP server. In these cases, [WebRTC](https://webrtc.org/) provides a peer-to-peer alternative, leveraging real-time communication capabilities, provided a signaling connection (e.g., via WebSockets or another channel) is established between the parties.

This repository implements a WebRTC-based transport layer compatible with the MCP specification, enabling seamless integration in constrained networking setups.

## Installation

### Python

```bash
pip install mcp-webrtc
```

### Typescript

```bash
npm install mcp-webrtc
```

## Example

For instance, a remote Agent-to-Agent (A2A) agent might need to leverage a local Model Context Protocol (MCP) server to access the filesystem on the A2A client's host. The A2A Protocol, developed by Google, enables secure inter-agent communication and complements MCP by facilitating agent-to-agent interactions. In this setup, the scenario unfolds as follows:

```mermaid
---
config:
  layout: dagre
  look: neo
  theme: mc
---
flowchart LR
    subgraph Local["Desktop"]
        direction TB
        AC["A2A Client"]
        MS["MCP Server"]
    end
    subgraph Remote["Cloud"]
        direction TB
        AS["A2A Server"]
        MC["MCP Client"]
    end
    AC <-- A2A --> AS
    MS <-- MCP --> MC
```

Directly connecting the MCP client on the remote A2A agent to the local MCP server over HTTP may be impractical due to Network Address Translation (NAT) traversal challenges or firewall restrictions. Even in scenarios without NATs, authentication is crucial to verify that the connection originates from the legitimate agent and no one else.

As an alternative, the established A2A connection serves as the signaling channel for WebRTC. It exchanges the necessary WebRTC signaling data (e.g., SDP offers/answers and ICE candidates), enabling a secure, peer-to-peer MCP connection to be established despite network constraints.

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
