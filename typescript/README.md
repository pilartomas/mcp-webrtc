# WebRTC Transport for Model Context Protocol

[The Model Context Protocol (MCP)](https://modelcontextprotocol.io) is an open standard for connecting AI applications to external systems, such as tools and data sources. It defines several transport mechanisms for client-server communication, including STDIO (over standard input/output) and Streamable HTTP (for web-based streaming).

However, there are scenarios—such as in browser environments or firewalled networks—where neither STDIO nor Streamable HTTP can effectively connect an MCP client to an MCP server. In these cases, [WebRTC](https://webrtc.org/) provides a peer-to-peer alternative, leveraging real-time communication capabilities, provided a signaling connection (e.g., via WebSockets or another channel) is established between the parties.

This repository implements a WebRTC-based transport layer compatible with the MCP specification, enabling seamless integration in constrained networking setups.

## Installation

```bash
npm install mcp-webrtc
```

## Usage

```typescript
  import { Client } from "@modelcontextprotocol/sdk/client/index.js";
  import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
  import { MemorySignaling, WebRTCClientTransport, WebRTCServerTransport } from "mcp-webrtc";
  import wrtc from "@roamhq/wrtc";

  const client = new Client({
    name: "example-client",
    version: "1.0.0",
  });

  const server = new McpServer({
    name: "example-server",
    version: "1.0.0",
  });
  server.registerTool("greet", {}, () => ({
    content: [{ type: "text", text: "Howdy" }],
  }));

  const [clientSignaling, serverSignaling] =
    await MemorySignaling.createMemorySignalingPair();

  const clientTransport = new WebRTCClientTransport({
    signaling: clientSignaling,
    peerOptions: {
      wrtc,
    },
  });
  const serverTransport = new WebRTCServerTransport({
    signaling: serverSignaling,
    peerOptions: {
      wrtc,
    },
  });

  await server.connect(serverTransport);
  await client.connect(clientTransport);

  const { tools } = await client.listTools();
  console.log(tools)

  await client.close();
  await server.close();
```
