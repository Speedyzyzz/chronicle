import { createHash } from "crypto";

export type CausalEventType =
  | "session_start"
  | "tool_call_input"
  | "tool_call_output"
  | "model_prompt"
  | "model_completion"
  | "fs_write"
  | "fs_read"
  | "subprocess_exec"
  | "env_read"
  | "session_end";

export interface CausalEvent {
  event_id: string;
  session_id: string;
  parent_event_id?: string | null;
  lamport_clock: number;
  vector_clock: Record<string, number>;
  event_type: CausalEventType;
  actor: string;
  payload: Record<string, unknown>;
  fs_state_blake3?: string | null;
  timestamp_ns: number;
}

export class LamportClock {
  private value = 0;

  public tick(): number {
    this.value += 1;
    return this.value;
  }

  public update(receivedTime: number): number {
    this.value = Math.max(this.value, receivedTime) + 1;
    return this.value;
  }

  public get current(): number {
    return this.value;
  }
}

export class ChronicleTracer {
  public readonly sessionId: string;
  public readonly actorId: string;
  private readonly clock = new LamportClock();
  private vectorClock: Record<string, number> = {};
  public headEventId: string | null = null;
  public recordedEvents: CausalEvent[] = [];

  constructor(sessionId: string, actorId = "node_agent") {
    this.sessionId = sessionId;
    this.actorId = actorId;
    this.vectorClock[actorId] = 0;
  }

  public recordEvent(
    eventType: CausalEventType,
    payload: Record<string, unknown>,
    fsStateBlake3?: string | null
  ): CausalEvent {
    const lamport = this.clock.tick();
    this.vectorClock[this.actorId] = lamport;

    const hashBody = JSON.stringify({
      session_id: this.sessionId,
      parent_event_id: this.headEventId,
      lamport_clock: lamport,
      vector_clock: this.vectorClock,
      event_type: eventType,
      actor: this.actorId,
      payload,
      fs_state_blake3: fsStateBlake3 || null,
    });

    const eventId = createHash("sha256").update(hashBody).digest("hex");
    const event: CausalEvent = {
      event_id: eventId,
      session_id: this.sessionId,
      parent_event_id: this.headEventId,
      lamport_clock: lamport,
      vector_clock: { ...this.vectorClock },
      event_type: eventType,
      actor: this.actorId,
      payload,
      fs_state_blake3: fsStateBlake3 || null,
      timestamp_ns: Date.now() * 1_000_000,
    };

    this.headEventId = eventId;
    this.recordedEvents.push(event);
    return event;
  }

  public recordToolCall(
    toolName: string,
    args: Record<string, unknown>,
    output: unknown
  ): CausalEvent {
    this.recordEvent("tool_call_input", { tool_name: toolName, arguments: args });
    return this.recordEvent("tool_call_output", { tool_name: toolName, output });
  }
}
