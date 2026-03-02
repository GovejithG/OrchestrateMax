import { useState, useEffect } from "react";
import {
  createSession,
  createTask,
  runTask,
  getExecutionEvents,
  getExecutionSummary,
} from "./api/client";

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [taskId, setTaskId] = useState(null);
  const [executionId, setExecutionId] = useState(null);
  const [taskTitle, setTaskTitle] = useState("");
  const [events, setEvents] = useState([]);
  const [summary, setSummary] = useState(null);

  // Poll events every 2 seconds
  useEffect(() => {
    if (!executionId) return;

    const interval = setInterval(async () => {
      try {
        const data = await getExecutionEvents(executionId);
        setEvents(data);

        const summaryData = await getExecutionSummary(executionId);
        setSummary(summaryData);
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [executionId]);

  const handleCreateSession = async () => {
    const data = await createSession();
    setSessionId(data.id);
  };

  const handleCreateTask = async () => {
    const data = await createTask(sessionId, taskTitle);
    setTaskId(data.id);
  };

  const handleRunTask = async () => {
    const data = await runTask(sessionId, taskId);
    setExecutionId(data.execution_id);
  };

  return (
    <div
      style={{
        padding: "2rem",
        fontFamily: "Arial",
        backgroundColor: "#0f0f0f",
        color: "#f5f5f5",
        minHeight: "100vh",
      }}
    >
      <h1 style={{ fontSize: "2.5rem", marginBottom: "1rem" }}>
        AI Orchestrator
      </h1>

      {/* Session */}
      <button
        onClick={handleCreateSession}
        style={buttonStyle}
      >
        Create Session
      </button>
      <p style={{ marginTop: "0.5rem" }}>
        <strong>Session:</strong> {sessionId}
      </p>

      {/* Task */}
      {sessionId && (
        <>
          <div style={{ marginTop: "1rem" }}>
            <input
              placeholder="Task title..."
              value={taskTitle}
              onChange={(e) => setTaskTitle(e.target.value)}
              style={inputStyle}
            />
            <button
              onClick={handleCreateTask}
              style={{ ...buttonStyle, marginLeft: "0.5rem" }}
            >
              Create Task
            </button>
          </div>
          <p>
            <strong>Task:</strong> {taskId}
          </p>
        </>
      )}

      {/* Run */}
      {taskId && (
        <>
          <button
            onClick={handleRunTask}
            style={buttonStyle}
          >
            Run Task
          </button>
          <p>
            <strong>Execution:</strong> {executionId}
          </p>
        </>
      )}

      {/* Events */}
      {executionId && (
        <>
          <h2 style={{ marginTop: "2rem" }}>Execution Events</h2>
          <pre style={eventPanelStyle}>
            {JSON.stringify(events, null, 2)}
          </pre>
        </>
      )}

      {/* Summary */}
      {summary && (
        <>
          <h2 style={{ marginTop: "2rem" }}>Execution Summary</h2>
          <pre style={summaryPanelStyle}>
            {JSON.stringify(summary, null, 2)}
          </pre>
        </>
      )}
    </div>
  );
}

/* ---------- Styles ---------- */

const buttonStyle = {
  padding: "8px 14px",
  backgroundColor: "#1f1f1f",
  color: "#ffffff",
  border: "1px solid #333",
  cursor: "pointer",
};

const inputStyle = {
  padding: "8px",
  backgroundColor: "#1a1a1a",
  color: "#ffffff",
  border: "1px solid #333",
  width: "250px",
};

const eventPanelStyle = {
  backgroundColor: "#1e1e1e",
  color: "#00ffcc",
  padding: "1rem",
  maxHeight: "300px",
  overflow: "auto",
  border: "1px solid #333",
};

const summaryPanelStyle = {
  backgroundColor: "#1e1e1e",
  color: "#ffd166",
  padding: "1rem",
  overflow: "auto",
  border: "1px solid #333",
};

export default App;