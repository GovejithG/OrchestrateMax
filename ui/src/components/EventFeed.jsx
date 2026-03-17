import { useEffect, useRef, useState } from "react";
import { ChevronDown, Filter } from "lucide-react";

const EVENT_STYLES = {
  AGENT_ROLE_STARTED: "text-violet-400",
  AGENT_ROLE_COMPLETED: "text-emerald-400",
  LLM_REQUEST: "text-zinc-500",
  LLM_RESPONSE: "text-zinc-400",
  TOOL_EXECUTION: "text-amber-400",
  FINAL_OUTPUT: "text-emerald-400 font-semibold",
  TASK_CANCELLED: "text-red-400",
  TASK_TIMEOUT: "text-red-400",
  MAX_ITERATIONS_REACHED: "text-orange-400",
  RETRY_SCHEDULED: "text-orange-400",
};

const EVENT_LABELS = {
  AGENT_ROLE_STARTED: (p) => `▶ ${p?.agent_role} agent started`,
  AGENT_ROLE_COMPLETED: (p) => `✓ ${p?.agent_role} agent completed`,
  LLM_REQUEST: (p) => `→ LLM call (iteration ${p?.iteration ?? "?"})`,
  LLM_RESPONSE: (p) => `← LLM response received`,
  TOOL_EXECUTION: (p) => `⚙ Tool: ${p?.tool}(${JSON.stringify(p?.arguments ?? {}).slice(0, 60)})`,
  FINAL_OUTPUT: () => `✦ Final output ready`,
  TASK_CANCELLED: () => `✕ Task cancelled`,
  TASK_TIMEOUT: () => `✕ Task timed out`,
  MAX_ITERATIONS_REACHED: () => `⚠ Max iterations reached`,
  RETRY_SCHEDULED: (p) => `↻ Retry scheduled (attempt ${p?.attempt_number})`,
};

export default function EventFeed({ events }) {
  const bottomRef = useRef(null);
  const [showLLM, setShowLLM] = useState(false);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  const filtered = showLLM
    ? events
    : events.filter((e) => !["LLM_REQUEST", "LLM_RESPONSE"].includes(e.event_type));

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b border-zinc-800">
        <span className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
          Event Feed
        </span>
        <button
          onClick={() => setShowLLM((v) => !v)}
          className={`flex items-center gap-1 text-xs px-2 py-1 rounded transition-colors ${
            showLLM
              ? "bg-zinc-700 text-zinc-200"
              : "text-zinc-500 hover:text-zinc-300"
          }`}
        >
          <Filter size={10} />
          LLM internals
        </button>
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-3 font-mono text-xs space-y-1">
        {filtered.length === 0 && (
          <p className="text-zinc-600 pt-4 text-center">
            Waiting for events...
          </p>
        )}
        {filtered.map((event, i) => {
          const labelFn = EVENT_LABELS[event.event_type];
          const label = labelFn
            ? labelFn(event.payload)
            : event.event_type;
          return (
            <div
              key={event.id || i}
              className={`${EVENT_STYLES[event.event_type] || "text-zinc-500"} leading-relaxed`}
            >
              <span className="text-zinc-700 mr-2">
                {event.created_at
                  ? new Date(event.created_at).toLocaleTimeString()
                  : ""}
              </span>
              {label}
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
