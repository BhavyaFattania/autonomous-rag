import type { DashboardState } from "../types";
import styles from "./BudgetOverviewPanel.module.css";

export function BudgetOverviewPanel({ state }: { state: DashboardState | null }) {
  const spent = state?.budget_spent ?? 0;
  const ceiling = state?.budget_ceiling ?? 0;
  const pct = ceiling > 0 ? Math.min(100, (spent / ceiling) * 100) : 0;
  const level = pct >= 95 ? "red" : pct >= 80 ? "amber" : "green";

  return (
    <div className={styles.panel}>
      <h3>Budget Overview</h3>
      <div className={styles.barTrack}>
        <div className={styles.barFill} data-level={level} style={{ width: `${pct}%` }} />
      </div>
      <div className={styles.row}>
        <span>Total Spent</span>
        <span className={styles.value}>${spent.toFixed(2)}</span>
      </div>
      <div className={styles.row}>
        <span>Budget Ceiling</span>
        <span className={styles.value}>${ceiling.toFixed(2)}</span>
      </div>
      <div className={styles.row}>
        <span>Remaining</span>
        <span className={styles.value}>${Math.max(0, ceiling - spent).toFixed(2)}</span>
      </div>
    </div>
  );
}
