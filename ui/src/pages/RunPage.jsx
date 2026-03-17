import { useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { createSSEConnection, getWorkspaceFiles } from "../api/client";
import useStore from "../store/useStore";
import PipelineView from "../components/PipelineView.jsx";
import EventFeed from "../components/EventFeed.jsx";
import ResultView from "../components/ResultView.jsx";
import WorkspacePanel from "../components/WorkspacePanel.jsx";

const TERMINAL_EVENTS = new Set([
  "FINAL_OUTPUT", "TASK_CANCELLED", "TASK_TIMEOUT", "MAX_ITERATIONS_REACHED"
]);

export default function RunPage() {
  const { executionId } = useParams();
  const navigate = useNavigate();
  const sseRef = useRef(null);
  const {
    events, addEvent, setAgentStage, resetAgentStages,
    runStatus, setRunStatus, setFinalOutput, setReviewerResult,
    setWorkspaceFiles, clearEvents, addSection, clearSections,
  } = useStore();

  useEffect(() => {
    if (!executionId) return;
    clearEvents();
    clearSections();
    resetAgentStages();
    setRunStatus("running");

    const sse = createSSEConnection(
      executionId,
      async (event) => {
        if (event.event_type === "HEARTBEAT") return;

        addEvent(event);

        if (event.event_type === "AGENT_SECTION_READY") {
            addSection(event.payload?.section, event.payload?.content);
        }

        if (event.event_type === "AGENT_ROLE_STARTED") {
          setAgentStage(event.payload?.agent_role, "running");
        }
        if (event.event_type === "AGENT_ROLE_COMPLETED") {
          setAgentStage(event.payload?.agent_role, "completed");
        }
        if (event.event_type === "FINAL_OUTPUT") {
          const output = event.payload?.final_output || "";
          setFinalOutput(output);
          parseReviewerOutput(output);
          setRunStatus("completed");
          const files = await getWorkspaceFiles();
          setWorkspaceFiles(files.files || []);
        }
        if (event.event_type === "TASK_CANCELLED") {
          setRunStatus("cancelled");
        }
        if (event.event_type === "TASK_TIMEOUT") {
          setRunStatus("failed");
        }
        if (event.event_type === "MAX_ITERATIONS_REACHED") {
          setRunStatus("failed");
        }
      },
      (err) => {
        console.error("SSE error:", err);
        const currentStatus = useStore.getState().runStatus;
        if (currentStatus !== "completed" && currentStatus !== "cancelled") {
            setRunStatus("failed");
        }
      }
    );

    sseRef.current = sse;
    return () => sse.close();
  }, [executionId]);

  const parseReviewerOutput = (text) => {
    const scoreMatch = text.match(/SCORE:\s*(\d+)\/10/i);
    const verdictMatch = text.match(/VERDICT:\s*(PASS|FAIL)/i);
    if (scoreMatch || verdictMatch) {
      setReviewerResult({
        score: scoreMatch ? parseInt(scoreMatch[1]) : null,
        verdict: verdictMatch ? verdictMatch[1] : null,
      });
    }
  };

  return (
    <div className="flex-1 flex flex-col gap-0">
      <div className="border-b border-zinc-800 px-6 py-4">
        <PipelineView executionId={executionId} />
      </div>
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-zinc-800 min-h-0">
        <div className="flex flex-col min-h-0 max-h-[70vh] lg:max-h-none">
          <EventFeed events={events} />
        </div>
        <div className="flex flex-col gap-0 divide-y divide-zinc-800">
          <div className="flex-1 overflow-auto p-4">
            <ResultView />
          </div>
          <div className="p-4">
            <WorkspacePanel />
          </div>
        </div>
      </div>
    </div>
  );
}
