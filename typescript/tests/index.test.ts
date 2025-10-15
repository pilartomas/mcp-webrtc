import { expect, test } from "vitest";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import {
  MemorySignaling,
  WebRTCClientTransport,
  WebRTCServerTransport,
} from "../src/index.js";
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

  // Connect
  await server.connect(serverTransport);
  await client.connect(clientTransport);

  // List tools
  const { tools } = await client.listTools();
  expect(tools.at(0)?.name).toBe("greet");

  await client.close();
  await server.close();
});
