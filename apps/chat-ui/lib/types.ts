export type Role = "user" | "assistant" | "system" | "tool";

export interface ToolCall {
  call_id: string;
  tool_name: string;
  args: Record<string, unknown>;
  result?: unknown;
}

export interface TraceMeta {
  run_id: string;
  run_url: string;
}

export interface Message {
  id: string;
  role: Role;
  content: string;
  tool_calls?: ToolCall[];
  trace?: TraceMeta;
}

export type StreamEvent =
  | { type: "token"; content: string }
  | { type: "tool_start"; tool_name: string; args: Record<string, unknown>; call_id: string }
  | { type: "tool_end"; call_id: string; result: unknown }
  | { type: "message_end"; finish_reason: string }
  | { type: "error"; message: string; code: string }
  | { type: "trace_meta"; run_url: string; run_id: string };
