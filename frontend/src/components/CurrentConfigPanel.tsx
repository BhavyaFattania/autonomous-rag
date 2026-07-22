import type { LiveEvent } from "../types";
import styles from "./SidePanel.module.css";

export function CurrentConfigPanel({ event }: { event: LiveEvent | null }) {
  const config = event?.config ?? {};
  return (
    <div className={styles.panel}>
      <h3>Current Configuration</h3>
      <dl>
        {Object.entries(config).map(([key, value]) => (
          <div key={key} className={styles.row}>
            <dt>{key}</dt>
            <dd>{String(value)}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
