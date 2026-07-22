// Mirrors src/core/events.py's ExperimentEvent (Pydantic model_dump(mode="json"))
export interface LiveEvent {
  experiment: number;
  node: string;
  status: string;
  timestamp: string;
  cost_total_usd: number;
  cost_ceiling_usd: number | null;
  message: string;
  hypothesis: string;
  reasoning: string;
  config: Record<string, unknown>;
  metrics: Record<string, number>;
  failure_reason: string;
  progress_current: number | null;
  progress_total: number | null;
}

// Mirrors src/web/schemas.py's ExperimentRowSchema
export interface ExperimentRow {
  experiment: number;
  status: string;
  score: number;
  cost: number;
}

// Mirrors src/web/schemas.py's FailureInfoSchema
export interface FailureInfo {
  node: string;
  status: string;
  failure_reason: string;
  timestamp: string;
}

// Mirrors src/web/schemas.py's DashboardStateSchema
export interface DashboardState {
  node_states: Record<string, string>;
  active_node: string | null;
  best_config: Record<string, unknown>;
  best_score: number;
  budget_spent: number;
  budget_ceiling: number | null;
  history: ExperimentRow[];
  last_failure: FailureInfo | null;
  pipeline_order: string[];
}

// The single message shape broadcast by GET /ws/live (see src/web/live.py)
export interface LivePayload {
  event: LiveEvent;
  state: DashboardState;
}
