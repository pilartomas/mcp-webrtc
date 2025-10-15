export abstract class BaseSignaling {
  abstract connect(): Promise<void>;

  abstract close(): Promise<void>;

  abstract send(data: unknown): Promise<void>;

  abstract receive(): AsyncGenerator<unknown>;
}
