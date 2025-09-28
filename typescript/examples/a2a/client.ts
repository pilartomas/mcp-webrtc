import { A2AClient } from "@a2a-js/sdk/client";
import { v4 as uuidv4 } from "uuid";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { WebRTCServerTransport } from "../../src/index.js";
import wrtc from "@roamhq/wrtc";
import type { DataPart } from "@a2a-js/sdk";

async function run() {
  const client = await A2AClient.fromCardUrl(
    "http://localhost:4000/.well-known/agent-card.json"
  );

  const server = new McpServer({
    name: "example-server",
    version: "1.0.0",
  });
  server.registerTool("greet", {}, () => ({
    content: [{ type: "text", text: "Howdy" }],
  }));
  const transport = new WebRTCServerTransport(
    async (data) => {
      for await (const event of await client.sendMessageStream({
        message: {
          messageId: uuidv4(),
          role: "user",
          parts: [{ kind: "data", data }],
          kind: "message",
        },
      })) {
        if (event.kind == "status-update") {
          if (event.status.state == "working" && event.status.message) {
            const dataPart = event.status.message?.parts.at(0) as DataPart;
            await transport.signal(dataPart.data);
          } else if (event.status.state == "completed") {
            console.log(event.status.message);
          }
        }
      }
    },
    { wrtc }
  );
  await server.connect(transport);

  //   await server.close();
}

await run();
