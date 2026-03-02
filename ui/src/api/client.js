const BASE_URL = "http://127.0.0.1:8000";

// -------------------------
// Helper
// -------------------------
async function handleResponse(res) {
    if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText);
    }
    return res.json();
}

// -------------------------
// Sessions
// -------------------------
export async function createSession(name) {
    const res = await fetch(`${BASE_URL}/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
    });

    return handleResponse(res);
}

// -------------------------
// Tasks
// -------------------------
export async function createTask(sessionId, title) {
    const res = await fetch(
        `${BASE_URL}/sessions/${sessionId}/tasks`,
        {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                title,
                description: "", // optional
            }),
        }
    );

    return handleResponse(res);
}

// -------------------------
// Run Execution
// -------------------------
export async function runTask(sessionId, taskId) {
    const res = await fetch(
        `${BASE_URL}/agent-run/${sessionId}/${taskId}`,
        {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_input: "Start execution", // adjust if backend expects real input
            }),
        }
    );

    return handleResponse(res);
}

// -------------------------
// Execution Events
// -------------------------
export async function getExecutionEvents(executionId) {
    const res = await fetch(
        `${BASE_URL}/executions/${executionId}/events`
    );

    return handleResponse(res);
}

// -------------------------
// Execution Summary
// -------------------------
export async function getExecutionSummary(executionId) {
    const res = await fetch(
        `${BASE_URL}/executions/${executionId}/summary`
    );

    return handleResponse(res);
}