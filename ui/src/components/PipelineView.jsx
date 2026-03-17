import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";
import useStore from "../store/useStore";

const AGENTS = [
  { key: "PLANNER", label: "Planner", description: "Plans the approach" },
  { key: "EXECUTOR", label: "Executor", description: "Writes the code" },
  { key: "REVIEWER", label: "Reviewer", description: "Reviews quality" },
];

const STATUS_STYLES = {
  idle: "text-zinc-600 border-zinc-800 bg-zinc-900",
  running: "text-violet-400 border-violet-500/50 bg-violet-500/10",
  completed: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10",
  failed: "text-red-400 border-red-500/30 bg-red-500/10",
};

const StatusIcon = ({ status }) => {
  if (status === "running") return <Loader2 size={14} className="animate-spin" />;
  if (status === "completed") return <CheckCircle2 size={14} />;
  if (status === "failed") return <XCircle size={14} />;
  return <Circle size={14} />;
};

export default function PipelineView({ executionId }) {
  const { agentStages, runStatus } = useStore();

  return (
    <div className="flex items-center gap-3 flex-wrap">
      <span className="text-xs text-zinc-500 font-mono mr-2 hidden sm:block">
        {executionId?.slice(0, 8)}...
      </span>
      {AGENTS.map((agent, i) => (
        <div key={agent.key} className="flex items-center gap-3">
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
              STATUS_STYLES[agentStages[agent.key]]
            }`}
          >
            <StatusIcon status={agentStages[agent.key]} />
            {agent.label}
          </div>
          {i < AGENTS.length - 1 && (
            <div className="text-zinc-700 text-sm">→</div>
          )}
        </div>
      ))}
      <div className="ml-auto">
        {runStatus === "running" && (
          <span className="text-xs text-violet-400 bg-violet-400/10 px-2 py-1 rounded-full font-medium animate-pulse">
            Live
          </span>
        )}
        {runStatus === "completed" && (
          <span className="text-xs text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded-full font-medium">
            Completed
          </span>
        )}
        {runStatus === "failed" && (
          <span className="text-xs text-red-400 bg-red-400/10 px-2 py-1 rounded-full font-medium">
            Failed
          </span>
        )}
        {runStatus === "cancelled" && (
          <span className="text-xs text-zinc-400 bg-zinc-400/10 px-2 py-1 rounded-full font-medium">
            Cancelled
          </span>
        )}
      </div>
    </div>
  );
}
