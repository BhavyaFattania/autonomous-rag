import type { DashboardState, LiveEvent } from "../types";
import styles from "./TopBar.module.css";

interface Props {
  event: LiveEvent | null;
  state: DashboardState | null;
  connected: boolean;
}

export function TopBar({ event, state, connected }: Props) {
  return (
    <header className={styles.topBar}>
      <div className={styles.title}>
        <h1>Autonomous RAG Optimizer</h1>
        <span className={styles.subtitle}>AI-Powered Experimentation Agent</span>
      </div>

      <div className={styles.currentExperiment}>
        {event && (
          <>
            <span className={styles.experimentNumber}>Experiment #{event.experiment}</span>
            <span className={styles.statusBadge} data-status={event.status}>
              {event.status}
            </span>
          </>
        )}
      </div>

      <div className={styles.stats}>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Total Cost</span>
          <span className={styles.statValue}>
            ${event?.cost_total_usd.toFixed(2) ?? "0.00"}
            {state?.budget_ceiling != null && ` of $${state.budget_ceiling.toFixed(2)}`}
          </span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Best Score</span>
          <span className={styles.statValue}>{state?.best_score.toFixed(3) ?? "--"}</span>
        </div>
      </div>

      <div className={styles.connectionIndicator} data-connected={connected}>
        {connected ? "Live" : "Reconnecting…"}
      </div>
    </header>
  );
}
