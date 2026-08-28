import type { TraceMeta } from "@/lib/types";

export function TraceLink({ trace }: { trace: TraceMeta }) {
  return (
    <a
      href={trace.run_url}
      target="_blank"
      rel="noopener noreferrer"
      style={{
        fontSize: 11,
        color: "var(--accent)",
        marginTop: 4,
        textDecoration: "none",
      }}
    >
      ↗ View trace in LangSmith ({trace.run_id.slice(0, 8)})
    </a>
  );
}
