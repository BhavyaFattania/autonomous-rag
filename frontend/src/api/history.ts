export interface RunSummary {
  run_id: string;
  started_at: string;
  finished_at: string | null;
  total_cost: number;
  n_experiments: number;
  n_accepted: number;
  best_config: string | null;
  best_score: number | null;
  status: string | null;
}

export interface ExperimentSummary {
  experiment_id: number;
  experiment_uuid: string;
  run_id: string;
  config_hash: string;
  config_json: string;
  hypothesis: string;
  status: string;
  failure_reason: string;
  metrics_json: string | null;
  baseline_score: number;
  proposed_score: number;
  cost_usd: number;
  started_at: string;
  finished_at: string | null;
  duration_sec: number | null;
}

export type ExperimentDetail = ExperimentSummary;

export interface NodeEventRecord {
  id: number;
  run_id: string;
  experiment_uuid: string;
  experiment_seq: number;
  node: string;
  status: string;
  timestamp: string;
  cost_total_usd: number;
  message: string;
  hypothesis: string;
  reasoning: string;
  config_json: string | null;
  metrics_json: string | null;
  failure_reason: string;
  progress_current: number | null;
  progress_total: number | null;
  raw_event_json: string | null;
}

export interface RunEventsFilters {
  node?: string;
  status?: string;
  beforeId?: number;
  limit?: number;
}

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${url} returned ${response.status}`);
  }
  return response.json();
}

export function fetchRuns(): Promise<RunSummary[]> {
  return getJson("/api/runs");
}

export function fetchRunExperiments(runId: string): Promise<ExperimentSummary[]> {
  return getJson(`/api/runs/${encodeURIComponent(runId)}/experiments`);
}

export function fetchExperiment(experimentId: number): Promise<ExperimentDetail> {
  return getJson(`/api/experiments/${experimentId}`);
}

export function fetchExperimentEvents(experimentUuid: string): Promise<NodeEventRecord[]> {
  return getJson(`/api/experiments/by-uuid/${encodeURIComponent(experimentUuid)}/events`);
}

export function fetchRunEvents(
  runId: string,
  filters: RunEventsFilters = {},
): Promise<NodeEventRecord[]> {
  const params = new URLSearchParams();
  if (filters.node) params.set("node", filters.node);
  if (filters.status) params.set("status", filters.status);
  if (filters.beforeId != null) params.set("before_id", String(filters.beforeId));
  if (filters.limit != null) params.set("limit", String(filters.limit));
  const qs = params.toString();
  return getJson(`/api/runs/${encodeURIComponent(runId)}/events${qs ? `?${qs}` : ""}`);
}
