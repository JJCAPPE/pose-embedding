"use client";

import { ArrowRightOutlined } from "@ant-design/icons";
import { Button, Empty, Listy, Progress, Segmented, Typography } from "antd";
import Link from "next/link";
import { useMemo, useState } from "react";
import { CurrentWeekMarker } from "@/components/current-week";
import { StatusLabel } from "@/components/status-label";
import { formatDateRange } from "@/lib/domain";
import type { TaskState, Week, WeekState } from "@/lib/schema";

const { Paragraph, Title } = Typography;

type Filter = "all" | "ready" | "active" | "blocked" | "closed";

export type TimelineWeek = Pick<
  Week,
  | "endDate"
  | "id"
  | "number"
  | "objective"
  | "phase"
  | "plannedMinutes"
  | "startDate"
  | "title"
> & {
  state: WeekState;
  tasks: { required: boolean; state: TaskState }[];
};

function timelineWeekIsReady(weeks: TimelineWeek[], weekNumber: number) {
  if (weekNumber === 1) return true;
  return weeks.find((week) => week.number === weekNumber - 1)?.state === "closed";
}

function timelineWeekProgress(week: TimelineWeek) {
  const required = week.tasks.filter((task) => task.required);
  const completed = required.filter((task) => task.state === "done");
  return {
    completed: completed.length,
    percent: required.length === 0 ? 0 : Math.round((completed.length / required.length) * 100),
    required: required.length,
  };
}

const FILTERS: { value: Filter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "ready", label: "Ready" },
  { value: "active", label: "Active" },
  { value: "blocked", label: "Blocked" },
  { value: "closed", label: "Closed" },
];

export function Timeline({ weeks, timezone }: { weeks: TimelineWeek[]; timezone: string }) {
  const [filter, setFilter] = useState<Filter>("all");
  const filtered = useMemo(
    () =>
      weeks.filter((week) => {
        if (filter === "all") return true;
        if (filter === "ready") return timelineWeekIsReady(weeks, week.number);
        return week.state === filter;
      }),
    [filter, weeks],
  );

  return (
    <section aria-labelledby="timeline-title" className="timeline-section">
      <div className="section-heading">
        <Title id="timeline-title" level={2}>
          The fourteen-week plan
        </Title>
        <Paragraph>
          Work state shows what is happening now. Prerequisites show whether the
          previous week has been closed.
        </Paragraph>
      </div>
      <div className="filter-row">
        <Segmented
          aria-label="Filter weeks by work state or prerequisite readiness"
          block
          onChange={(value) => setFilter(value as Filter)}
          options={FILTERS}
          value={filter}
        />
      </div>
      {filtered.length > 0 ? (
        <div role="list">
          <Listy
            className="timeline-list"
            itemRender={(week) => {
              const progress = timelineWeekProgress(week);
              const ready = timelineWeekIsReady(weeks, week.number);
              return (
                <div className="timeline-item" role="listitem">
              <Link className="week-link" href={`/weeks/${week.number}`}>
                <div className="week-index" aria-hidden="true">
                  {String(week.number).padStart(2, "0")}
                </div>
                <div className="week-summary">
                  <div className="week-summary-topline">
                    <span>{week.phase}</span>
                    <span>{formatDateRange(week.startDate, week.endDate)}</span>
                  </div>
                  <h3>{week.title}</h3>
                  <p>{week.objective}</p>
                  <div className="week-meta">
                    <span className="metric-label">Work state</span>
                    <StatusLabel status={week.state} />
                    <span className="metric-label">Prerequisites</span>
                    <StatusLabel status={ready ? "ready" : "not_ready"} />
                    <span>{week.plannedMinutes / 60}h planned</span>
                    <CurrentWeekMarker
                      startDate={week.startDate}
                      endDate={week.endDate}
                      timezone={timezone}
                    />
                  </div>
                  <div className="week-progress">
                    <Progress
                      aria-label={`${progress.completed} of ${progress.required} required tasks complete`}
                      percent={progress.percent}
                      showInfo={false}
                      size="small"
                    />
                    <span>
                      {progress.completed}/{progress.required} required tasks
                    </span>
                  </div>
                </div>
                <span className="week-open" aria-hidden="true">
                  Open <ArrowRightOutlined />
                </span>
              </Link>
                </div>
              );
            }}
            items={filtered}
            rowKey="id"
          />
        </div>
      ) : (
        <Empty
          description="No weeks match this filter."
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          <Button onClick={() => setFilter("all")} type="link">
            Show the full plan
          </Button>
        </Empty>
      )}
    </section>
  );
}
