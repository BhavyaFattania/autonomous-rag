import type { DashboardState, LiveEvent } from "../types";
import { computeConfigDiff } from "../utils/configDiff";
import styles from "./ConfigDiffCard.module.css";

interface Props {
  event: LiveEvent | null;
  state: DashboardState | null;
}

export function ConfigDiffCard({ event, state }: Props) {
  if (!event?.config || Object.keys(event.config).length === 0) return null;
  const rows = computeConfigDiff(event.config, state?.best_config ?? {});

  return (
    <div className={styles.card}>
      <h3>Live Configuration (Diff vs Best)</h3>
      <table>
        <tbody>
          {rows.map((row) => (
            <tr key={row.field}>
              <td>{row.field}</td>
              <td>{String(row.value)}</td>
              <td data-note={row.note}>{row.note}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
