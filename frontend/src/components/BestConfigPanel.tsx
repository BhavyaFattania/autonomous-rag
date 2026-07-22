import type { DashboardState } from "../types";
import styles from "./SidePanel.module.css";

export function BestConfigPanel({ state }: { state: DashboardState | null }) {
  return (
    <div className={styles.panel}>
      <h3>Best Configuration (So Far)</h3>
      <div className={styles.row}>
        <dt>Score</dt>
        <dd>{state?.best_score.toFixed(3) ?? "--"}</dd>
      </div>
      <dl>
        {Object.entries(state?.best_config ?? {}).map(([key, value]) => (
          <div key={key} className={styles.row}>
            <dt>{key}</dt>
            <dd>{String(value)}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
