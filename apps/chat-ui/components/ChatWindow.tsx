"use client";

import { useState, useRef, useEffect } from "react";
import { streamChat } from "@/lib/api";
import type { Message, ToolCall } from "@/lib/types";
import { MessageBubble } from "./MessageBubble";

let nextId = 0;
const newId = () => `msg-${++nextId}`;

export function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages]);

  async function send() {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setBusy(true);

    const userMsg: Message = { id: newId(), role: "user", content: text };
    const assistantMsg: Message = {
      id: newId(),
      role: "assistant",
      content: "",
      tool_calls: [],
    };
    const history = [...messages, userMsg];
    setMessages([...history, assistantMsg]);

    const accumulated: Message = { ...assistantMsg };
    const toolCalls = new Map<string, ToolCall>();

    abortRef.current = new AbortController();
    try {
      for await (const event of streamChat(
        history.map((m) => ({
          // history only ever contains user/assistant messages; Role's "tool"
          // variant is for messages never placed into conversation history.
          role: m.role as "user" | "assistant" | "system",
          content: m.content,
        })),
        abortRef.current.signal,
      )) {
        if (event.type === "token") {
          accumulated.content += event.content;
        } else if (event.type === "tool_start") {
          toolCalls.set(event.call_id, {
            call_id: event.call_id,
            tool_name: event.tool_name,
            args: event.args,
          });
        } else if (event.type === "tool_end") {
          const existing = toolCalls.get(event.call_id);
          if (existing) {
            existing.result = event.result;
          }
        } else if (event.type === "trace_meta") {
          accumulated.trace = { run_id: event.run_id, run_url: event.run_url };
        } else if (event.type === "error") {
          accumulated.content += `\n\n[error: ${event.message}]`;
        }
        accumulated.tool_calls = Array.from(toolCalls.values());
        // Force a re-render with the latest accumulated state
        setMessages((prev) => {
          const next = [...prev];
          next[next.length - 1] = { ...accumulated };
          return next;
        });
      }
    } finally {
      setBusy(false);
      abortRef.current = null;
    }
  }

  function stop() {
    abortRef.current?.abort();
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 48px)" }}>
      <div ref={scrollRef} style={{ flex: 1, overflowY: "auto", padding: "0 4px" }}>
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
      </div>
      <div
        style={{
          display: "flex",
          gap: 8,
          padding: "12px 0",
          borderTop: "1px solid var(--border)",
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          placeholder={busy ? "Generating..." : "Type a message and press Enter"}
          disabled={busy}
          style={{
            flex: 1,
            padding: "10px 12px",
            borderRadius: 8,
            border: "1px solid var(--border)",
            background: "var(--bg)",
            color: "var(--fg)",
          }}
        />
        {busy ? (
          <button onClick={stop}>Stop</button>
        ) : (
          <button
            onClick={send}
            style={{
              background: "var(--accent)",
              color: "white",
              border: 0,
              borderRadius: 8,
              padding: "0 16px",
              cursor: "pointer",
            }}
          >
            Send
          </button>
        )}
      </div>
    </div>
  );
}
