"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { CurrentWeekMarker } from "@/components/current-week";
import { StatusLabel } from "@/components/status-label";
import { formatDateRange, weekIsReady, weekProgress } from "@/lib/domain";
import type { Week } from "@/lib/schema";

type Filter = "all" | "ready" | "active" | "blocked" | "closed";

const FILTERS: { value: Filter; label: string }[] = [
  { value: "all", label: "All weeks" },
  { value: "ready", label: "Ready" },
  { value: "active", label: "Active" },
  { value: "blocked", label: "Blocked" },
  { value: "closed", label: "Closed" },
];

export function Timeline({ weeks, timezone }: { weeks: Week[]; timezone: string }) {
  const [filter, setFilter] = useState<Filter>("all");
  const filtered = useMemo(
    () =>
      weeks.filter((week) => {
        if (filter === "all") return true;
        if (filter === "ready") return weekIsReady(weeks, week.number);
        return week.state === filter;
      }),
    [filter, weeks],
  );

  return (
    <section aria-labelledby="timeline-title" className="timeline-section">
      <div className="section-heading">
        <h2 id="timeline-title">Fourteen weekly gates</h2>
        <p>Open a week for its work, evidence requirements, risks, and exit criteria.</p>
      </div>
      <div className="filter-row" role="group" aria-label="Filter weeks by state">
        {FILTERS.map((item) => (
          <button
            aria-pressed={filter === item.value}
            className="filter-button"
            key={item.value}
            onClick={() => setFilter(item.value)}
            type="button"
          >
            {item.label}
          </button>
        ))}
      </div>
      {filtered.length === 0 ? (
        <div className="empty-state">
          <h3>No weeks match this filter.</h3>
          <button className="text-button" onClick={() => setFilter("all")} type="button">
            Show the full plan
          </button>
        </div>
      ) : (
        <ol className="timeline-list">
          {filtered.map((week) => {
            const progress = weekProgress(week);
            const ready = weekIsReady(weeks, week.number);
            return (
              <li className="timeline-item" key={week.id}>
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
                      <StatusLabel status={week.state} />
                      <StatusLabel status={ready ? "ready" : "not_ready"} />
                      <span>{week.plannedMinutes / 60}h planned</span>
                      <span>
                        {progress.completed}/{progress.required} required tasks
                      </span>
                      <CurrentWeekMarker
                        startDate={week.startDate}
                        endDate={week.endDate}
                        timezone={timezone}
                      />
                    </div>
                  </div>
                  <span className="week-open" aria-hidden="true">View</span>
                </Link>
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
