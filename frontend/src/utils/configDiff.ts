// TypeScript port of src/core/config_diff.py's compute_config_diff -- same
// pure logic, kept in sync manually since there's no cross-language import.
// If the Python version's behavior changes, update this to match.
export interface ConfigDiffRow {
  field: string;
  value: unknown;
  note: string;
}

export function computeConfigDiff(
  current: Record<string, unknown>,
  best: Record<string, unknown>
): ConfigDiffRow[] {
  const rows: ConfigDiffRow[] = [];
  for (const [key, curVal] of Object.entries(current)) {
    const bestVal = best[key];
    if (curVal === bestVal) {
      rows.push({ field: key, value: curVal, note: "same" });
    } else if (typeof curVal === "number" && typeof bestVal === "number") {
      const arrow = curVal > bestVal ? "↑" : "↓";
      rows.push({ field: key, value: curVal, note: `${arrow} from ${bestVal}` });
    } else {
      rows.push({ field: key, value: curVal, note: "changed" });
    }
  }
  return rows;
}
