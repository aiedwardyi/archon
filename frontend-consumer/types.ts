
export interface Project {
  id: string;
  name: string;
  description: string;
  createdAt: number;
  status: 'IDLE' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  currentStage: AgentStage;
  engineerTasks?: EngineerTask[];
}

export type AgentStage = 'idle' | 'pm' | 'planner' | 'engineer' | 'complete';

export type Language = 'en' | 'ko';

export interface EngineerTask {
  id: string;
  filename: string;
  timestamp: number;
  description: string;
}

export interface Artifact {
  id: string;
  projectId: string;
  type: 'PRD' | 'PLAN' | 'CODE';
  title: string;
  content: any; // JSON content
  createdAt: number;
  agent: string;
}

export interface LogEntry {
  id: string;
  projectId: string;
  timestamp: number;
  message: string;
  type: 'info' | 'success' | 'error' | 'system';
}

// Responses from Agents
export interface PrdResponse {
  title: string;
  summary: string;
  features: string[];
  userStories: string[];
  techStackRecommendation: string[];
}

export interface PlanResponse {
  phases: {
    name: string;
    description: string;
    steps: string[];
  }[];
  estimatedTimeline: string;
}

export interface CodeFile {
  filename: string;
  content: string;
  language: string;
}

export interface CodeResponse {
  files: CodeFile[];
  setupInstructions: string;
}

export interface SystemSettings {
  theme: 'dark' | 'light';
  language: Language;
}
