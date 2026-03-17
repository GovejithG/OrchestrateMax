import { create } from "zustand";

const useStore = create((set, get) => ({
  // Sessions
  sessions: [],
  setSessions: (sessions) => set({ sessions }),

  // Current run
  currentSessionId: null,
  currentTaskId: null,
  currentExecutionId: null,
  setCurrentRun: (sessionId, taskId, executionId) =>
    set({ currentSessionId: sessionId, currentTaskId: taskId, currentExecutionId: executionId }),

  // Events
  events: [],
  addEvent: (event) => set((state) => ({ events: [...state.events, event] })),
  clearEvents: () => set({ events: [] }),

  // Sections
  sections: [],  // each entry: { section: "PLAN"|"CODE"|"REVIEW", content: string }
  addSection: (section, content) =>
    set((state) => ({
      sections: [...state.sections, { section, content }],
    })),
  clearSections: () => set({ sections: [] }),

  // Pipeline stage tracking
  agentStages: {
    PLANNER: "idle",    // idle | running | completed | failed
    EXECUTOR: "idle",
    REVIEWER: "idle",
  },
  setAgentStage: (role, status) =>
    set((state) => ({
      agentStages: { ...state.agentStages, [role]: status },
    })),
  resetAgentStages: () =>
    set({ agentStages: { PLANNER: "idle", EXECUTOR: "idle", REVIEWER: "idle" } }),

  // Run status
  runStatus: "idle",  // idle | running | completed | failed | cancelled
  setRunStatus: (status) => set({ runStatus: status }),

  // Final output
  finalOutput: null,
  setFinalOutput: (output) => set({ finalOutput: output }),

  // Reviewer result parsed
  reviewerResult: null,
  setReviewerResult: (result) => set({ reviewerResult: result }),

  // Workspace files
  workspaceFiles: [],
  setWorkspaceFiles: (files) => set({ workspaceFiles: files }),

  // Reset everything for a new run
  resetRun: () =>
    set({
      events: [],
      sections: [],
      runStatus: "idle",
      finalOutput: null,
      reviewerResult: null,
      workspaceFiles: [],
      agentStages: { PLANNER: "idle", EXECUTOR: "idle", REVIEWER: "idle" },
    }),
}));

export default useStore;
