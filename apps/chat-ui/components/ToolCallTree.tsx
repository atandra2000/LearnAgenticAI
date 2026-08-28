"use client";

import { useState } from "react";
import type { ToolCall } from "@/lib/types";

export function ToolCallTree({ call }: { call: ToolCall }) {
  const [open, setOpen] = useState(false);
  return (
    <div
      style={{
        fontSize: 12,
        background: "var(--bg)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "6px 10px",
        marginTop: 4,
      }}
    >
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          background: "transparent",
          border: 0,
          color: "var(--accent)",
          cursor: "pointer",
          padding: 0,
          fontSize: 12,
        }}
      >
        {open ? "▼" : "▶"} {call.tool_name} ({call.call_id.slice(0, 8)})
      </button>
      {open && (
        <pre
          style={{
            margin: "6px 0 0",
            fontSize: 11,
            color: "var(--muted)",
            whiteSpace: "pre-wrap",
          }}
        >
          args: {JSON.stringify(call.args, null, 2)}
          {"\n"}
          {call.result !== undefined && `result: ${JSON.stringify(call.result, null, 2)}`}
        </pre>
      )}
    </div>
  );
}
