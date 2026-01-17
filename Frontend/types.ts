export enum SystemState {
  IDLE = 'IDLE',
  ANALYZING = 'ANALYZING', // Represents "Thinking" or "Recursively Processing"
  DECISION_READY = 'DECISION_READY', // Represents "Waiting" or "Response Complete"
  ERROR = 'ERROR'
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export type ChatHistory = ChatMessage[];