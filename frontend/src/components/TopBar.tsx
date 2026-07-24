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
      <div className={styles.brand}>
        <svg className={styles.mark} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M12 2 21 7v10l-9 5-9-5V7z"
            stroke="currentColor"
            strokeWidth="1.4"
            strokeLinejoin="round"
          />
          <circle cx="12" cy="12" r="3" fill="currentColor" />
        </svg>
        <div className={styles.title}>
          <h1>Autonomous RAG Optimizer</h1>
          <span className={styles.subtitle}>AI-Powered Experimentation Agent</span>
        </div>
      </div>

      <div className={styles.currentExperiment}>
        {event && (
          <>
            <span className={styles.experimentNumber}>Experiment #{event.experiment}</span>
            <span className={styles.statusBadge} data-status={event.status}>
              <span className={styles.statusDot} />
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
            {state?.budget_ceiling != null && (
              <span className={styles.statSuffix}> / ${state.budget_ceiling.toFixed(2)}</span>
            )}
          </span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Best Score</span>
          <span className={styles.statValue} data-accent="amber">
            {state?.best_score.toFixed(3) ?? "--"}
          </span>
        </div>
      </div>

      <div className={styles.connectionIndicator} data-connected={connected}>
        <span className={styles.liveDot} />
        {connected ? "Live" : "Reconnecting…"}
      </div>
    </header>
  );
}
