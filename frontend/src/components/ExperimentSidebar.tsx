import type { DashboardState } from "../types";
import styles from "./ExperimentSidebar.module.css";

interface Props {
  state: DashboardState | null;
  onViewAll: () => void;
  onSelectExperiment: (experimentUuid: string) => void;
}

export function ExperimentSidebar({ state, onViewAll, onSelectExperiment }: Props) {
  const rows = [...(state?.history ?? [])].reverse();

  return (
    <aside className={styles.sidebar}>
      <div className={styles.heading}>
        <h3>Experiments</h3>
        <span className={styles.count}>{rows.length}</span>
      </div>
      <ul>
        {rows.map((row) => (
          <li key={row.experiment}>
            <button
              className={styles.row}
              data-status={row.status}
              disabled={!row.experiment_uuid}
              onClick={() => row.experiment_uuid && onSelectExperiment(row.experiment_uuid)}
            >
              <span className={styles.number}>#{row.experiment}</span>
              <span className={styles.status}>{row.status.toLowerCase()}</span>
              <span className={styles.score}>{row.score.toFixed(3)}</span>
            </button>
          </li>
        ))}
      </ul>
      <button className={styles.viewAll} onClick={onViewAll}>
        View All Experiments
      </button>
    </aside>
  );
}
