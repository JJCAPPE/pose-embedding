"use client";

import { Statistic } from "antd";

export function SummaryMetrics({
  completedRequiredTasks,
  decidedRequiredGates,
  percent,
  requiredGates,
  requiredTasks,
}: {
  completedRequiredTasks: number;
  decidedRequiredGates: number;
  percent: number;
  requiredGates: number;
  requiredTasks: number;
}) {
  return (
    <div className="summary-metrics" aria-label="Project progress summary">
      <Statistic title="Plan complete" value={percent} suffix="%" />
      <Statistic
        title="Required tasks"
        value={completedRequiredTasks}
        suffix={`/ ${requiredTasks}`}
      />
      <Statistic
        title="Gate decisions"
        value={decidedRequiredGates}
        suffix={`/ ${requiredGates}`}
      />
    </div>
  );
}
