const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface SSEEvent {
  type: "content" | "tool_start" | "tool_end" | "done" | "error";
  data?: string;
  tool?: string;
  message?: string;
}

/**
 * Stream chat messages from the FlowPay Agent via SSE.
 * Yields parsed SSEEvent objects as they arrive.
 */
export async function* streamChat(
  message: string,
  threadId: string
): AsyncGenerator<SSEEvent> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ message, thread_id: threadId }),
  });

  if (!res.ok) {
    yield { type: "error", message: `Server error: ${res.status}` };
    return;
  }

  const reader = res.body?.getReader();
  if (!reader) {
    yield { type: "error", message: "No response stream" };
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || !trimmed.startsWith("data: ")) continue;

      const jsonStr = trimmed.slice(6);
      try {
        const parsed = JSON.parse(jsonStr);
        // Content can be a string or an array of objects with a .text field
        if (parsed.type === "content") {
          let text = "";
          if (typeof parsed.data === "string") {
            text = parsed.data;
          } else if (Array.isArray(parsed.data)) {
            text = parsed.data
              .map((d: { text?: string }) => d.text || "")
              .join("");
          }
          yield { type: "content", data: text };
        } else {
          yield parsed as SSEEvent;
        }
      } catch {
        // Ignore malformed JSON
      }
    }
  }
}
