
import { PrdResponse, PlanResponse, CodeResponse } from "../types";

/**
 * MOCKUP ENGINE
 * These functions simulate the processing delay and intelligence of AI agents.
 * In a production environment, these would call the Gemini API.
 */

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const generatePRD = async (idea: string): Promise<PrdResponse> => {
  // Simulate "Thinking" delay
  await sleep(2500);

  const title = idea.split(' ').slice(0, 3).join(' ') || "Neural Application";

  return {
    title: `${title} - Core Requirements`,
    summary: `A high-performance application based on the user's request: "${idea}". This platform focuses on modular scalability and intuitive user experience.`,
    features: [
      "User Authentication with OAuth2 integration",
      "Real-time data visualization dashboard",
      "Collaborative workspace for team members",
      "Automated reporting and export functionality",
      "Cross-platform responsive design system"
    ],
    userStories: [
      "As a user, I want to securely log in so that my data is protected.",
      "As a developer, I want a clean API so that I can extend the platform.",
      "As a manager, I want to see real-time progress of my team."
    ],
    techStackRecommendation: [
      "Frontend: React 19 + TypeScript",
      "Styling: Tailwind CSS",
      "State Management: React Context + Query",
      "Backend: Node.js / Express",
      "Database: PostgreSQL / Prisma"
    ]
  };
};

export const generatePlan = async (prd: PrdResponse): Promise<PlanResponse> => {
  // Simulate "Thinking" delay for Architect agent
  await sleep(3000);

  return {
    phases: [
      {
        name: "Foundation & Infrastructure",
        description: "Setting up the project core and shared utilities.",
        steps: [
          "Initialize TypeScript React environment",
          "Configure Tailwind design tokens",
          "Setup base routing and layout components"
        ]
      },
      {
        name: "Feature Implementation",
        description: "Building out the core modules defined in the PRD.",
        steps: [
          "Develop Authentication context",
          "Build Data Visualization engine",
          "Integrate real-time socket connections"
        ]
      },
      {
        name: "Final Assembly & QA",
        description: "Polishing the UI and ensuring cross-browser compatibility.",
        steps: [
          "Perform automated unit testing",
          "Audit accessibility (ARIA) and performance",
          "Deploy to staging environment"
        ]
      }
    ],
    estimatedTimeline: "2-3 Development Cycles"
  };
};

export const generateCode = async (plan: PlanResponse, prd: PrdResponse): Promise<CodeResponse> => {
  // Simulate "Thinking" delay for Engineer agent
  await sleep(4000);

  return {
    files: [
      {
        filename: "App.tsx",
        language: "typescript",
        content: `import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import Sidebar from './components/Sidebar';

export default function App() {
  const [data, setData] = useState([]);
  
  useEffect(() => {
    // Simulated data fetch for ${prd.title}
    console.log("Initializing application modules...");
  }, []);

  return (
    <div className="flex h-screen bg-slate-900 text-white font-sans">
      <Sidebar />
      <main className="flex-1 overflow-auto p-8">
        <header className="mb-8">
          <h1 className="text-4xl font-black">${prd.title}</h1>
          <p className="text-slate-400 mt-2">v1.0.0-beta</p>
        </header>
        <Dashboard />
      </main>
    </div>
  );
}`
      },
      {
        filename: "components/Dashboard.tsx",
        language: "typescript",
        content: `import React from 'react';
import { Activity, Users, Database } from 'lucide-react';

export default function Dashboard() {
  const stats = [
    { label: 'Active Users', value: '1,284', icon: Users },
    { label: 'System Uptime', value: '99.9%', icon: Activity },
    { label: 'Database Load', value: '12%', icon: Database },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {stats.map((stat, i) => (
        <div key={i} className="p-6 bg-slate-800 rounded-3xl border border-white/5 hover:border-blue-500/50 transition-all">
          <div className="flex items-center gap-4 mb-4">
            <stat.icon className="text-blue-500" />
            <span className="text-xs font-bold uppercase tracking-widest text-slate-400">{stat.label}</span>
          </div>
          <div className="text-3xl font-black">{stat.value}</div>
        </div>
      ))}
    </div>
  );
}`
      },
      {
        filename: "styles/theme.ts",
        language: "typescript",
        content: `export const theme = {
  colors: {
    primary: '#3b82f6',
    secondary: '#8b5cf6',
    accent: '#10b981',
    background: '#0f172a'
  },
  spacing: {
    base: '1rem',
    large: '2rem'
  }
};`
      }
    ],
    setupInstructions: "Run 'npm install' followed by 'npm run dev' to launch the local development server. Ensure environment variables for the database connection are configured in .env."
  };
};
