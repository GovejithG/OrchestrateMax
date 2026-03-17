import { Outlet, NavLink } from "react-router-dom";
import { Bot, History, Github } from "lucide-react";

export default function Layout() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col">
      <header className="border-b border-zinc-800 px-6 py-3 flex items-center gap-4">
        <div className="flex items-center gap-2 font-bold text-white text-lg tracking-tight">
          <Bot size={20} className="text-violet-400" />
          OrchestrateMax
        </div>
        <nav className="flex items-center gap-1 ml-6">
          <NavLink
            to="/"
            className={({ isActive }) =>
              `px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                isActive
                  ? "bg-zinc-800 text-white"
                  : "text-zinc-400 hover:text-white hover:bg-zinc-800/50"
              }`
            }
          >
            New Run
          </NavLink>
          <NavLink
            to="/history"
            className={({ isActive }) =>
              `px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
                isActive
                  ? "bg-zinc-800 text-white"
                  : "text-zinc-400 hover:text-white hover:bg-zinc-800/50"
              }`
            }
          >
            <History size={14} />
            History
          </NavLink>
        </nav>
        <div className="ml-auto text-xs text-zinc-600 font-mono">v0.2.0</div>
      </header>
      <main className="flex-1 flex flex-col">
        <Outlet />
      </main>
    </div>
  );
}
