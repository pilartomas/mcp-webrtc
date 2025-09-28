import SimplePeer from "simple-peer";
import type {
  Transport,
  TransportSendOptions,
} from "@modelcontextprotocol/sdk/shared/transport.js";
import type { JSONRPCMessage } from "@modelcontextprotocol/sdk/types.js";

class WebRTCTransport implements Transport {
  public peer?: SimplePeer.Instance;

  onclose?: () => void;
  onerror?: (error: Error) => void;
  onmessage?: (message: JSONRPCMessage) => void;

  constructor(
    private onSignal: (data: any) => void,
    private readonly options?: SimplePeer.Options
  ) {}

  async start(): Promise<void> {
    this.peer = new SimplePeer(this.options);
    this.peer.on("data", (data) => {
      this.onmessage?.(JSON.parse(data));
    });
    this.peer.on("close", () => {
      this.onclose?.();
    });
    this.peer.on("error", (err) => {
      this.onerror?.(err);
    });
    this.peer.on("signal", (data) => {
      this.onSignal(data);
    });
  }

  async send(message: JSONRPCMessage, options?: TransportSendOptions) {
    if (!this.peer) throw new Error("Transport hasn't started");
    if (!this.peer.connected)
      await new Promise((res, rej) => this.peer?.on("connect", res));
    this.peer.send(JSON.stringify(message));
  }

  signal(data: any) {
    if (!this.peer) throw new Error("Transport hasn't started");
    this.peer.signal(data);
  }

  async close() {
    if (!this.peer) throw new Error("Transport hasn't started");
    this.peer.end();
  }
}

export class WebRTCClientTransport extends WebRTCTransport {
  constructor(onSignal: (data: any) => void, options?: SimplePeer.Options) {
    super(onSignal, { ...options, initiator: false });
  }
}

export class WebRTCServerTransport extends WebRTCTransport {
  constructor(onSignal: (data: any) => void, options?: SimplePeer.Options) {
    super(onSignal, { ...options, initiator: true });
  }
}
