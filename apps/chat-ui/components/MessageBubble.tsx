import type { Message } from "@/lib/types";
import { ToolCallTree } from "./ToolCallTree";
import { TraceLink } from "./TraceLink";

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: isUser ? "flex-end" : "flex-start",
        margin: "12px 0",
      }}
    >
      <div
        style={{
          maxWidth: "80%",
          padding: "10px 14px",
          borderRadius: 12,
          background: isUser ? "var(--bubble-user)" : "var(--bubble-assistant)",
          border: "1px solid var(--border)",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
        }}
      >
        <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 4 }}>
          {message.role}
        </div>
        <div>{message.content}</div>
        {message.tool_calls && message.tool_calls.length > 0 && (
          <div style={{ marginTop: 8 }}>
            {message.tool_calls.map((tc) => (
              <ToolCallTree key={tc.call_id} call={tc} />
            ))}
          </div>
        )}
      </div>
      {message.trace && <TraceLink trace={message.trace} />}
    </div>
  );
}
