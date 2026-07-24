import { useEffect, useState } from "react";
import { fetchExperiment, type ExperimentDetail } from "../api/history";
import styles from "./ExperimentDetailPage.module.css";

interface Props {
  experimentId: number;
  onBack: () => void;
}

export function ExperimentDetailPage({ experimentId, onBack }: Props) {
  const [experiment, setExperiment] = useState<ExperimentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchExperiment(experimentId)
      .then(setExperiment)
      .catch(() => setError("Failed to load experiment"));
  }, [experimentId]);

  if (error) {
    return (
      <div className={styles.page}>
        <button className={styles.back} onClick={onBack}>
          ← Back to runs
        </button>
        <p className={styles.error}>{error}</p>
      </div>
    );
  }

  if (!experiment) return null;

  const config = JSON.parse(experiment.config_json || "{}");
  const metrics = experiment.metrics_json ? JSON.parse(experiment.metrics_json) : {};

  return (
    <div className={styles.page}>
      <button className={styles.back} onClick={onBack}>
        ← Back to runs
      </button>
      <h2>
        Experiment #{experiment.experiment_id}{" "}
        <span className={styles.status}>{experiment.status.toLowerCase()}</span>
      </h2>
      <p className={styles.hypothesis}>{experiment.hypothesis}</p>

      <h3>Config</h3>
      <pre>{JSON.stringify(config, null, 2)}</pre>

      <h3>Metrics</h3>
      <pre>{JSON.stringify(metrics, null, 2)}</pre>
    </div>
  );
}
