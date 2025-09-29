import { expect, test } from "vitest";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { WebRTCClientTransport, WebRTCServerTransport } from "../src/index.js";
import wrtc from "@roamhq/wrtc";

test("client connects to server and lists tools", async () => {
  // Prepare client
  const client = new Client({
    name: "example-client",
    version: "1.0.0",
  });

  // Prepare server
  const server = new McpServer({
    name: "example-server",
    version: "1.0.0",
  });
  server.registerTool("greet", {}, () => ({
    content: [{ type: "text", text: "Howdy" }],
  }));

  const clientTransport = new WebRTCClientTransport({
    onSignal: async (data) => {
      await serverTransport.signal(data);
    },
    peerOptions: {
      wrtc,
    },
  });
  const serverTransport = new WebRTCServerTransport({
    onSignal: async (data) => {
      await clientTransport.signal(data);
    },
    peerOptions: {
      wrtc,
    },
  });

  // Connect
  await server.connect(serverTransport);
  await client.connect(clientTransport);

  // List tools
  const { tools } = await client.listTools();
  expect(tools.at(0)?.name).toBe("greet");
});
