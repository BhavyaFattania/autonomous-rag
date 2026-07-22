import type { DashboardState } from "../types";
import styles from "./PipelineStrip.module.css";

interface Props {
  state: DashboardState | null;
}

export function PipelineStrip({ state }: Props) {
  const order = state?.pipeline_order ?? [];

  return (
    <div className={styles.strip}>
      {order.map((node, index) => {
        const status = state?.node_states[node];
        const isActive = state?.active_node === node;
        return (
          <div key={node} className={styles.nodeWrapper}>
            <div
              className={styles.node}
              data-active={isActive}
              data-status={status ?? "pending"}
            >
              <span className={styles.nodeName}>{node}</span>
              <span className={styles.nodeStatus}>{status ?? "Pending"}</span>
            </div>
            {index < order.length - 1 && <div className={styles.connector} />}
          </div>
        );
      })}
    </div>
  );
}
