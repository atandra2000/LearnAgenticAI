import type { StreamEvent } from "./types";

/**
 * Stream a chat completion from the local agent backend.
 *
 * The backend speaks an SSE protocol on /v1/chat/completions. Each event
 * has a `type` field matching one of the StreamEvent variants.
 */
export async function* streamChat(
  messages: { role: "user" | "assistant" | "system"; content: string }[],
  signal?: AbortSignal,
): AsyncGenerator<StreamEvent, void, void> {
  const response = await fetch("/v1/chat/completions", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ messages, stream: true }),
    signal,
  });

  if (!response.ok || !response.body) {
    yield { type: "error", message: `HTTP ${response.status}`, code: "http_error" };
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let currentEvent = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let lineEnd = buffer.indexOf("\n");
    while (lineEnd !== -1) {
      const line = buffer.slice(0, lineEnd);
      buffer = buffer.slice(lineEnd + 1);
      if (line.startsWith("event: ")) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith("data: ")) {
        const data = line.slice(6);
        try {
          const parsed = JSON.parse(data);
          yield { type: currentEvent, ...parsed } as StreamEvent;
        } catch {
          // Skip malformed lines
        }
        currentEvent = "";
      } else if (line === "") {
        currentEvent = "";
      }
      lineEnd = buffer.indexOf("\n");
    }
  }
}
