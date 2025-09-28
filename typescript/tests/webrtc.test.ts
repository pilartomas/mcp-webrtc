import { expect, test } from "vitest";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { WebRTCClientTransport, WebRTCServerTransport } from "../src/index.js";

test("client connects to server and lists tools", async () => {
  // Prepare client
  const client = new Client({
    name: "example-client",
    version: "1.0.0",
  });
  const clientTransport = new WebRTCClientTransport();

  // Prepare server
  const server = new McpServer({
    name: "example-server",
    version: "1.0.0",
  });
  server.registerTool("greet", {}, () => ({
    content: [{ type: "text", text: "Howdy" }],
  }));
  const serverTransport = new WebRTCServerTransport();

  // SIGNAL exchange would happen e.g. through A2A protocol
  clientTransport.onsignal = (data) => serverTransport.signal(data);
  serverTransport.onsignal = (data) => clientTransport.signal(data);

  // Connect
  await server.connect(serverTransport);
  await client.connect(clientTransport);

  // List tools
  const { tools } = await client.listTools();
  expect(tools.at(0)?.name).toBe("greet");
});
