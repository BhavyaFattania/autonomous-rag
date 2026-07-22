import { useEffect, useState } from "react";
import { fetchRunExperiments, fetchRuns, type ExperimentSummary, type RunSummary } from "../api/history";
import styles from "./RunsListPage.module.css";

interface Props {
  onSelectExperiment: (experimentId: number) => void;
  onBack: () => void;
}

export function RunsListPage({ onSelectExperiment, onBack }: Props) {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([]);

  useEffect(() => {
    fetchRuns().then(setRuns);
  }, []);

  useEffect(() => {
    if (!selectedRun) return;
    fetchRunExperiments(selectedRun).then(setExperiments);
  }, [selectedRun]);

  return (
    <div className={styles.page}>
      <button onClick={onBack}>← Back to live view</button>
      <h2>All Runs</h2>
      <table>
        <thead>
          <tr>
            <th>Run</th>
            <th>Started</th>
            <th>Experiments</th>
            <th>Accepted</th>
            <th>Best Score</th>
            <th>Total Cost</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr
              key={run.run_id}
              onClick={() => setSelectedRun(run.run_id)}
              data-selected={run.run_id === selectedRun}
            >
              <td>{run.run_id}</td>
              <td>{new Date(run.started_at).toLocaleString()}</td>
              <td>{run.n_experiments}</td>
              <td>{run.n_accepted}</td>
              <td>{run.best_score?.toFixed(3) ?? "--"}</td>
              <td>${run.total_cost.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {selectedRun && (
        <>
          <h3>Experiments in {selectedRun}</h3>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Status</th>
                <th>Hypothesis</th>
                <th>Score</th>
                <th>Cost</th>
              </tr>
            </thead>
            <tbody>
              {experiments.map((exp) => (
                <tr key={exp.experiment_id} onClick={() => onSelectExperiment(exp.experiment_id)}>
                  <td>{exp.experiment_id}</td>
                  <td>{exp.status}</td>
                  <td>{exp.hypothesis}</td>
                  <td>{exp.proposed_score.toFixed(3)}</td>
                  <td>${exp.cost_usd.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
