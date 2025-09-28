import express from "express";
import { v4 as uuidv4 } from "uuid";
import type { AgentCard, DataPart, Message, Task } from "@a2a-js/sdk";
import {
  type AgentExecutor,
  RequestContext,
  type ExecutionEventBus,
  DefaultRequestHandler,
  InMemoryTaskStore,
} from "@a2a-js/sdk/server";
import { A2AExpressApp } from "@a2a-js/sdk/server/express";
import { Client } from "@modelcontextprotocol/sdk/client";
import wrtc from "@roamhq/wrtc";
import { WebRTCClientTransport } from "../../src/index.js";

const mcpAgentCard = {
  name: "MCP WebRTC Agent",
  description: "A simple agent that connects to an MCP server via WebRTC",
  protocolVersion: "0.3.0",
  version: "0.1.0",
  url: "http://localhost:4000/",
  skills: [],
  capabilities: { streaming: true },
  defaultInputModes: [],
  defaultOutputModes: [],
} satisfies AgentCard;

class MCPExecutor implements AgentExecutor {
  async execute(
    requestContext: RequestContext,
    eventBus: ExecutionEventBus
  ): Promise<void> {
    const { taskId, contextId } = requestContext;

    const userMessage = requestContext.userMessage;
    const dataPart = userMessage.parts.at(0) as DataPart;

    const initialTask: Task = {
      kind: "task",
      id: taskId,
      contextId: contextId,
      status: {
        state: "submitted",
        timestamp: new Date().toISOString(),
      },
    };
    eventBus.publish(initialTask);

    const client = new Client({
      name: "example-client",
      version: "1.0.0",
    });
    const transport = new WebRTCClientTransport(
      (data) => {
        eventBus.publish({
          kind: "status-update",
          contextId,
          taskId,
          status: {
            state: "working",
            message: {
              kind: "message",
              messageId: uuidv4(),
              role: "agent",
              parts: [{ kind: "data", data }],
            },
          },
          final: false,
        });
      },
      { wrtc }
    );
    await client.connect(transport);
    transport.signal(dataPart.data);
    const { tools } = await client.listTools();

    eventBus.publish({
      kind: "status-update",
      contextId,
      taskId,
      status: {
        state: "working",
        message: {
          kind: "message",
          messageId: uuidv4(),
          role: "agent",
          parts: tools.map((tool) => ({ kind: "text", text: tool.name })),
        },
      },
      final: false,
    });
    eventBus.finished();
  }

  // cancelTask is not needed for this simple, non-stateful agent.
  cancelTask = async (): Promise<void> => {};
}

const appBuilder = new A2AExpressApp(
  new DefaultRequestHandler(
    mcpAgentCard,
    new InMemoryTaskStore(),
    new MCPExecutor()
  )
);
const expressApp = appBuilder.setupRoutes(express());

expressApp.listen(4000, () => {
  console.log(`🚀 Server started on http://localhost:4000`);
});
