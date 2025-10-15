import SimplePeer from "simple-peer";
import type {
  Transport,
  TransportSendOptions,
} from "@modelcontextprotocol/sdk/shared/transport.js";
import {
  JSONRPCMessageSchema,
  type JSONRPCMessage,
} from "@modelcontextprotocol/sdk/types.js";
import type { BaseSignaling } from "./signaling/index.js";

export interface WebRTCTransportOptions {
  signaling: BaseSignaling;
  peerOptions?: SimplePeer.Options;
}

export class WebRTCTransport implements Transport {
  private peer?: SimplePeer.Instance;

  onclose?: () => void;
  onerror?: (error: Error) => void;
  onmessage?: (message: JSONRPCMessage) => void;

  constructor(private readonly options: WebRTCTransportOptions) {}

  async start(): Promise<void> {
    this.peer = new SimplePeer(this.options.peerOptions);
    this.peer.on("data", (data) => {
      try {
        const message = JSONRPCMessageSchema.parse(JSON.parse(data));
        this.onmessage?.(message);
      } catch (err) {
        this.onerror?.(err as Error);
      }
    });
    this.peer.on("close", () => {
      try {
        this.onclose?.();
      } catch (err) {
        console.error("close callback failed", err);
      }
    });
    this.peer.on("error", (err) => {
      try {
        this.onerror?.(err);
      } catch (err) {
        console.error("error callback failed", err);
      }
    });
    this.peer.on("signal", async (data) => {
      try {
        await this.options.signaling.send(data);
      } catch (err) {
        console.error("signal callback failed", err);
      }
    });
    await this.options.signaling.connect();
    (async () => {
      try {
        for await (const data of this.options.signaling.receive()) {
          this.peer?.signal(data);
        }
      } catch (err) {
        console.error("An exeption has occurred during signaling", err);
      }
    })();
  }

  async send(message: JSONRPCMessage, options?: TransportSendOptions) {
    if (!this.peer) throw new Error("Transport hasn't started");
    if (!this.peer.connected)
      await new Promise((res, rej) => {
        this.peer?.once("connect", res);
        this.peer?.once("close", rej);
      });
    this.peer.send(JSON.stringify(message));
  }

  async close() {
    if (!this.peer) throw new Error("Transport hasn't started");
    await this.options.signaling.close();
    this.peer.end();
  }
}

export class WebRTCClientTransport extends WebRTCTransport {
  constructor(options: WebRTCTransportOptions) {
    super({
      ...options,
      peerOptions: { ...options.peerOptions, initiator: false },
    });
  }
}

export class WebRTCServerTransport extends WebRTCTransport {
  constructor(options: WebRTCTransportOptions) {
    super({
      ...options,
      peerOptions: { ...options.peerOptions, initiator: true },
    });
  }
}
