const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function handleResponse(res) {
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(errorText);
  }
  return res.json();
}

export async function createSession(name) {
  const res = await fetch(`${BASE_URL}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  return handleResponse(res);
}

export async function createTask(sessionId, title, description) {
  const res = await fetch(`${BASE_URL}/sessions/${sessionId}/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, description }),
  });
  return handleResponse(res);
}

export async function runTask(sessionId, taskId, userInput) {
  const res = await fetch(`${BASE_URL}/agent-run/${sessionId}/${taskId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_input: userInput }),
  });
  return handleResponse(res);
}

export async function getSessions() {
  const res = await fetch(`${BASE_URL}/sessions`);
  return handleResponse(res);
}

export async function getSessionTasks(sessionId) {
  const res = await fetch(`${BASE_URL}/sessions/${sessionId}/tasks`);
  return handleResponse(res);
}

export async function getExecutionEvents(executionId) {
  const res = await fetch(`${BASE_URL}/executions/${executionId}/events`);
  return handleResponse(res);
}

export async function getExecutionSummary(executionId) {
  const res = await fetch(`${BASE_URL}/executions/${executionId}/summary`);
  return handleResponse(res);
}

export async function getWorkspaceFiles() {
  const res = await fetch(`${BASE_URL}/workspace/files`);
  return handleResponse(res);
}

export async function clearWorkspace() {
  const res = await fetch(`${BASE_URL}/workspace`, { method: "DELETE" });
  return handleResponse(res);
}

export function createSSEConnection(executionId, onEvent, onError) {
  const url = `${BASE_URL}/executions/${executionId}/stream`;
  const es = new EventSource(url);
  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      onEvent(data);
    } catch (err) {
      console.error("SSE parse error:", err);
    }
  };
  es.onerror = (e) => {
    onError(e);
    es.close();
  };
  return es;
}

export function getFileDownloadUrl(filePath) {
  return `${BASE_URL}/workspace/files/${filePath}`;
}