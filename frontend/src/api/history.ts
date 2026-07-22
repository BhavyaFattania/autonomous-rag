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
