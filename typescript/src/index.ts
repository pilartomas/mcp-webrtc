import SimplePeer from "simple-peer";
import type {
  Transport,
  TransportSendOptions,
} from "@modelcontextprotocol/sdk/shared/transport.js";
import {
  JSONRPCMessageSchema,
  type JSONRPCMessage,
} from "@modelcontextprotocol/sdk/types.js";

export interface WebRTCTransportOptions {
  onSignal: (data: any) => Promise<void> | void;
  onStart?: () => Promise<void> | void;
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
      this.onmessage?.(JSONRPCMessageSchema.parse(JSON.parse(data)));
    });
    this.peer.on("close", () => {
      this.onclose?.();
    });
    this.peer.on("error", (err) => {
      this.onerror?.(err);
    });
    this.peer.on("signal", async (data) => {
      try {
        await this.options.onSignal(data);
      } catch (err) {
        console.error("onSignal callback", err);
      }
    });
    await this.options.onStart?.();
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

  async signal(data: any) {
    if (!this.peer) throw new Error("Transport hasn't started");
    this.peer.signal(data);
  }

  async close() {
    if (!this.peer) throw new Error("Transport hasn't started");
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
