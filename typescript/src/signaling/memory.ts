import { BaseSignaling } from "./base.js";

export class MemorySignaling extends BaseSignaling {
  private closed = false;

  constructor(
    private readonly sendBuffer: unknown[],
    private readonly receiveBuffer: unknown[]
  ) {
    super();
  }

  async connect() {}

  async close() {
    this.closed = true;
  }

  async send(data: unknown) {
    if (this.closed) throw new Error("Signaling closed");
    this.sendBuffer.push(data);
  }

  async *receive() {
    while (!this.closed || this.receiveBuffer.length > 0) {
      if (this.receiveBuffer.length > 0) yield this.receiveBuffer.shift();
      else await new Promise((res) => setTimeout(res, 500)); // Dummy implementation
    }
  }

  static async createMemorySignalingPair(): Promise<
    [MemorySignaling, MemorySignaling]
  > {
    const one: any[] = [];
    const two: any[] = [];
    return [new MemorySignaling(one, two), new MemorySignaling(two, one)];
  }
}
