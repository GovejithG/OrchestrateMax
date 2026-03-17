import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Clock, ChevronRight, Loader2 } from "lucide-react";
import { getSessions, getSessionTasks } from "../api/client";

const STATUS_COLORS = {
  completed: "text-emerald-400 bg-emerald-400/10",
  failed: "text-red-400 bg-red-400/10",
  running: "text-violet-400 bg-violet-400/10",
  created: "text-zinc-400 bg-zinc-400/10",
  cancelled: "text-zinc-500 bg-zinc-500/10",
};

export default function HistoryPage() {
  const [sessions, setSessions] = useState([]);
  const [tasks, setTasks] = useState({});
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
        try {
            const data = await getSessions();
            if (cancelled) return;
            setSessions(data);

            const taskMap = {};
            for (const s of data) {
                if (cancelled) return;
                try {
                    const t = await getSessionTasks(s.id);
                    taskMap[s.id] = t;
                } catch {
                    taskMap[s.id] = [];
                }
            }

            if (!cancelled) {
                setTasks(taskMap);
                setLoading(false);
            }
        } catch (err) {
            if (!cancelled) {
                console.error("Failed to load history:", err);
                setLoading(false);
            }
        }
    };

    load();

    return () => {
        cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center flex-1">
        <Loader2 size={20} className="animate-spin text-zinc-500" />
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <Clock size={32} className="text-zinc-700 mx-auto mb-3" />
          <p className="text-zinc-500 text-sm">No runs yet</p>
          <button
            onClick={() => navigate("/")}
            className="mt-4 text-sm text-violet-400 hover:text-violet-300 transition-colors"
          >
            Start your first run →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 w-full">
      <h1 className="text-lg font-semibold text-white mb-6">Run History</h1>
      <div className="space-y-3">
        {sessions.map((session) => {
          const sessionTasks = tasks[session.id] || [];
          return (
            <div
              key={session.id}
              className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 hover:border-zinc-600 transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">
                    {session.name || "Unnamed session"}
                  </p>
                  <p className="text-xs text-zinc-500 mt-0.5 font-mono">
                    {new Date(session.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
              {sessionTasks.length > 0 && (
                <div className="mt-3 space-y-1.5">
                  {sessionTasks.map((task) => (
                    <div
                      key={task.id}
                      className="flex items-center gap-2 text-xs"
                    >
                      <span
                        className={`px-2 py-0.5 rounded-full font-medium ${
                          STATUS_COLORS[task.status] || STATUS_COLORS.created
                        }`}
                      >
                        {task.status}
                      </span>
                      <span className="text-zinc-400 truncate">{task.title}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
