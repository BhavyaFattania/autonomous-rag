import type { DashboardState } from "../types";
import styles from "./PipelineStrip.module.css";

interface Props {
  state: DashboardState | null;
  onSelectNode: (experimentUuid: string, node: string) => void;
}

export function PipelineStrip({ state, onSelectNode }: Props) {
  const order = state?.pipeline_order ?? [];
  const currentExperimentUuid = state?.current_experiment_uuid;

  return (
    <div className={styles.strip}>
      {order.map((node, index) => {
        const status = state?.node_states[node];
        const isActive = state?.active_node === node;
        const isDone = !isActive && !!status && status !== "PENDING";
        return (
          <div key={node} className={styles.nodeWrapper}>
            <button
              className={styles.node}
              data-active={isActive}
              data-status={status ?? "pending"}
              disabled={!currentExperimentUuid}
              onClick={() => currentExperimentUuid && onSelectNode(currentExperimentUuid, node)}
            >
              <span className={styles.badge} aria-hidden="true">
                {isActive ? (
                  <span className={styles.spinner} />
                ) : isDone ? (
                  <svg viewBox="0 0 16 16" width="12" height="12">
                    <path
                      d="M3 8.5 6.2 12 13 4"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      fill="none"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                ) : (
                  <span className={styles.dot} />
                )}
              </span>
              <span className={styles.nodeName}>{node.replace(/_/g, " ")}</span>
              <span className={styles.nodeStatus}>
                {isActive ? status : isDone ? "Done" : (status ?? "Pending")}
              </span>
            </button>
            {index < order.length - 1 && (
              <div className={styles.connector} data-charged={isDone}>
                <div className={styles.connectorFill} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
