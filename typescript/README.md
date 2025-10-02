# WebRTC Transport for Model Context Protocol

[The Model Context Protocol (MCP)](https://modelcontextprotocol.io) is an open standard for connecting AI applications to external systems, such as tools and data sources. It defines several transport mechanisms for client-server communication, including STDIO (over standard input/output) and Streamable HTTP (for web-based streaming).

However, there are scenarios—such as in browser environments or firewalled networks—where neither STDIO nor Streamable HTTP can effectively connect an MCP client to an MCP server. In these cases, [WebRTC](https://webrtc.org/) provides a peer-to-peer alternative, leveraging real-time communication capabilities, provided a signaling connection (e.g., via WebSockets or another channel) is established between the parties.

This repository implements a WebRTC-based transport layer compatible with the MCP specification, enabling seamless integration in constrained networking setups.

## Installation

```bash
npm install mcp-webrtc
```

# Usage

```typescript
  import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
  import { WebRTCServerTransport } from "mcp-webrtc";

  const server = new McpServer({
    name: "example-server",
    version: "1.0.0",
  });
  server.registerTool("greet", {}, () => ({
    content: [{ type: "text", text: "Howdy" }],
  }));
  await server.connect(new WebRTCServerTransport({
    onSignal: async (data) => { 
      // forward data via signalling channel and call peer.signal(data)
    }
  }));
```

```typescript
  import { Client } from "@modelcontextprotocol/sdk/client/index.js";
  import { WebRTCClientTransport } from "mcp-webrtc";

  const client = new Client({
    name: "example-client",
    version: "1.0.0",
  });
  await client.connect(new WebRTCClientTransport({
    onSignal: async (data) => { 
      // forward data via signalling channel and call peer.signal(data)
    }
  }));
```

Proceed by exchange the signalling data via arbitrary connection.