import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Loader2, Sparkles } from "lucide-react";
import { createSession, createTask, runTask } from "../api/client";
import useStore from "../store/useStore";

const EXAMPLE_PROMPTS = [
  "Write a Python function that finds all prime numbers up to N using the Sieve of Eratosthenes",
  "Create a REST API endpoint in Python that validates email addresses using regex",
  "Write a Python script that reads a CSV file and outputs basic statistics for each column",
  "Build a simple stack data structure in Python with push, pop, and peek methods",
];

export default function HomePage() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const { setCurrentRun, resetRun } = useStore();

  const handleSubmit = async () => {
    if (!prompt.trim() || loading) return;
    setLoading(true);
    setError(null);
    resetRun();
    try {
      const session = await createSession(prompt.slice(0, 60));
      const task = await createTask(session.id, prompt.slice(0, 100), prompt);
      const run = await runTask(session.id, task.id, prompt);
      setCurrentRun(session.id, task.id, run.execution_id);
      navigate(`/run/${run.execution_id}`);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmit();
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 py-16">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 text-violet-400 text-sm font-medium mb-4 bg-violet-400/10 px-3 py-1 rounded-full">
            <Sparkles size={14} />
            3-Agent Coding Pipeline
          </div>
          <h1 className="text-4xl font-bold text-white mb-3 tracking-tight">
            What should I build?
          </h1>
          <p className="text-zinc-400 text-base">
            Describe your coding task. The Planner, Executor, and Reviewer agents will handle the rest.
          </p>
        </div>

        <div className="bg-zinc-900 border border-zinc-700 rounded-xl overflow-hidden focus-within:border-violet-500 transition-colors">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe the code you want to build..."
            rows={5}
            className="w-full bg-transparent px-4 pt-4 pb-2 text-zinc-100 placeholder-zinc-500 text-sm resize-none outline-none"
          />
          <div className="flex items-center justify-between px-4 py-3 border-t border-zinc-800">
            <span className="text-xs text-zinc-600">⌘ + Enter to run</span>
            <button
              onClick={handleSubmit}
              disabled={!prompt.trim() || loading}
              className="flex items-center gap-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              {loading ? (
                <><Loader2 size={14} className="animate-spin" /> Starting...</>
              ) : (
                <><ArrowRight size={14} /> Run Pipeline</>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-4 bg-red-900/30 border border-red-700 text-red-300 text-sm px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        <div className="mt-8">
          <p className="text-xs text-zinc-600 mb-3 uppercase tracking-wider font-medium">
            Example prompts
          </p>
          <div className="grid gap-2">
            {EXAMPLE_PROMPTS.map((ex, i) => (
              <button
                key={i}
                onClick={() => setPrompt(ex)}
                className="text-left text-sm text-zinc-400 hover:text-zinc-200 px-3 py-2 rounded-lg hover:bg-zinc-800/50 transition-colors border border-transparent hover:border-zinc-700"
              >
                {ex}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
