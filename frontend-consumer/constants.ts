import { AgentStage } from './types';

export const AGENT_STAGES: { [key in AgentStage]: string } = {
  idle: 'Ready to Start',
  pm: 'PM Agent (Defining Requirements)',
  planner: 'Planner Agent (Architecting Solution)',
  engineer: 'Engineer Agent (Generating Code)',
  complete: 'Development Complete'
};

export const MOCK_DELAY_MS = 1500; // Simulated network/processing delay for effect

export const SYSTEM_INSTRUCTIONS = {
  PM: `You are an expert Product Manager. 
  Your goal is to take a raw user idea and convert it into a structured Product Requirement Document (PRD) in JSON format.
  Focus on clarity, feasibility, and core features.`,
  
  PLANNER: `You are an expert Engineering Planner and Architect.
  Your goal is to take a PRD and create a step-by-step technical execution plan in JSON format.
  Break down the work into logical phases.`,
  
  ENGINEER: `You are a Senior Software Engineer.
  Your goal is to take an execution plan and generate the actual code files for a prototype in JSON format.
  The output should contain a list of files with their content.`
};