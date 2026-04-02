// Types for Soccer Data RapidAPI integration

export interface SoccerDataResponse<T = unknown> {
  status: string;
  endpoint: string;
  data: T;
  error?: string;
}

export interface SoccerDataHealth {
  configured: boolean;
  status: string;
  message: string;
}

// Generic type for raw API explorer responses
export type ExplorerData = Record<string, unknown>;
