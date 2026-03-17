import { useState } from "react";
import { FolderOpen, Download, Trash2, RefreshCw } from "lucide-react";
import { getWorkspaceFiles, clearWorkspace, getFileDownloadUrl } from "../api/client";
import useStore from "../store/useStore";

export default function WorkspacePanel() {
  const { workspaceFiles, setWorkspaceFiles } = useStore();
  const [clearing, setClearing] = useState(false);

  const handleRefresh = async () => {
    const data = await getWorkspaceFiles();
    setWorkspaceFiles(data.files || []);
  };

  const handleClear = async () => {
    setClearing(true);
    await clearWorkspace();
    setWorkspaceFiles([]);
    setClearing(false);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5 text-xs font-medium text-zinc-400 uppercase tracking-wider">
          <FolderOpen size={12} />
          Workspace Files
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            className="text-zinc-500 hover:text-zinc-300 transition-colors"
          >
            <RefreshCw size={12} />
          </button>
          <button
            onClick={handleClear}
            disabled={clearing || workspaceFiles.length === 0}
            className="text-zinc-500 hover:text-red-400 disabled:opacity-30 transition-colors"
          >
            <Trash2 size={12} />
          </button>
        </div>
      </div>
      {workspaceFiles.length === 0 ? (
        <p className="text-xs text-zinc-600">No files yet</p>
      ) : (
        <div className="space-y-1">
          {workspaceFiles.map((file) => (
            <div
              key={file}
              className="flex items-center justify-between py-1 px-2 rounded hover:bg-zinc-800 group"
            >
              <span className="text-xs text-zinc-400 font-mono truncate">{file}</span>
              <a
                href={getFileDownloadUrl(file)}
                download
                className="text-zinc-600 hover:text-violet-400 transition-colors opacity-0 group-hover:opacity-100"
              >
                <Download size={12} />
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
