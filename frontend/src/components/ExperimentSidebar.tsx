import type { DashboardState } from "../types";
import styles from "./ExperimentSidebar.module.css";

export function ExperimentSidebar({ state }: { state: DashboardState | null }) {
  const rows = [...(state?.history ?? [])].reverse();

  return (
    <aside className={styles.sidebar}>
      <h3>Experiments</h3>
      <ul>
        {rows.map((row) => (
          <li key={row.experiment} data-status={row.status}>
            <span className={styles.number}>#{row.experiment}</span>
            <span className={styles.status}>{row.status}</span>
            <span className={styles.score}>{row.score.toFixed(3)}</span>
          </li>
        ))}
      </ul>
    </aside>
  );
}
