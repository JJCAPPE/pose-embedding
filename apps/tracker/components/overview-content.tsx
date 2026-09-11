import Link from "next/link";
import { DataNotice } from "@/components/data-notice";
import { PriorityBrief } from "@/components/priority-brief";
import { SummaryMetrics } from "@/components/summary-metrics";
import { Timeline } from "@/components/timeline";
import {
  formatDateRange,
  projectProgress,
  recentCompletedTasks,
  weekProgress,
} from "@/lib/domain";
import type { LoadedPlan } from "@/lib/schema";

export function OverviewContent({ plan }: { plan: LoadedPlan }) {
  const progress = projectProgress(plan);
  const recentCompletions = recentCompletedTasks(plan);
  const completionTime = new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: plan.project.timezone,
  });
  const openWeek = plan.weeks.find((week) => week.state !== "closed");
  const nextWeek = openWeek ?? plan.weeks.at(-1)!;
  const nextWeekProgress = weekProgress(nextWeek);
  const nextRequiredGates = nextWeek.gates.filter(
    (gate) => gate.required && gate.state === "pending",
  );
  const nextVerb = !openWeek
    ? "Review"
    : nextWeek.state === "active"
      ? "Continue"
      : nextWeek.state === "blocked"
        ? "Unblock"
        : "Start";
  const timelineWeeks = plan.weeks.map((week) => ({
    endDate: week.endDate,
    id: week.id,
    number: week.number,
    objective: week.objective,
    phase: week.phase,
    plannedMinutes: week.plannedMinutes,
    startDate: week.startDate,
    state: week.state,
    tasks: week.tasks.map(({ required, state }) => ({ required, state })),
    title: week.title,
  }));

  return (
    <div className="shell page-shell">
      <DataNotice dataSource={plan.dataSource} lastRefreshedAt={plan.lastRefreshedAt} />

      <header className="page-header">
        <div>
          <p className="eyebrow">Fourteen weeks · Fall 2026</p>
          <h1>From protocol lock to a result you can defend.</h1>
          <p className="page-summary">
            Work through one week at a time. Each week shows what to do, what to
            deliver, and what must be decided before moving forward.
          </p>
        </div>
      </header>

      <PriorityBrief
        actionHref={`/weeks/${nextWeek.number}`}
        actionLabel={`${nextVerb} Week ${nextWeek.number}`}
        decision={
          nextRequiredGates.length > 0 ? (
            <ol>
              {nextRequiredGates.map((gate, index) => (
                <li key={gate.id}>
                  <span className="decision-index" aria-hidden="true">
                    {index + 1}
                  </span>
                  <span>{gate.criterion}</span>
                </li>
              ))}
            </ol>
          ) : (
            <p className="muted">
              Every required gate for this week already has a decision.
            </p>
          )
        }
        deliverable={<p>{nextWeek.deliverable}</p>}
        nextDescription={`${formatDateRange(nextWeek.startDate, nextWeek.endDate)} · ${nextWeek.objective}`}
        nextTitle={`${nextVerb} Week ${nextWeek.number}: ${nextWeek.title}`}
        progress={{
          label: `${nextWeekProgress.completed} of ${nextWeekProgress.required} required tasks complete`,
          percent: nextWeekProgress.percent,
        }}
      />

      <section aria-labelledby="progress-title">
        <div className="section-heading compact">
          <h2 id="progress-title">Progress, at a glance</h2>
          <p>
            Progress records what is complete. It does not replace the evidence
            and decisions required to close a week.
          </p>
        </div>
        <SummaryMetrics {...progress} />
      </section>

      <section aria-labelledby="recent-completions-title" className="recent-completions-section">
        <div className="section-heading compact">
          <h2 id="recent-completions-title">Recent completions</h2>
          <p>The latest finished work and the public record that supports it.</p>
        </div>
        {recentCompletions.length > 0 ? (
          <ol className="recent-list">
            {recentCompletions.map(({ completedAt, task, weekNumber, weekTitle }) => (
              <li key={task.id}>
                <div className="recent-completion-copy">
                  <p className="recent-completion-week">
                    Week {weekNumber} · {weekTitle}
                  </p>
                  <h3>{task.title}</h3>
                </div>
                <div className="recent-completion-meta">
                  <time dateTime={completedAt}>{completionTime.format(new Date(completedAt))}</time>
                  <div className="recent-completion-links">
                    <Link href={`/weeks/${weekNumber}`}>View weekly record</Link>
                    {task.evidenceUrl ? (
                      <a href={task.evidenceUrl} rel="noreferrer" target="_blank">
                        Open evidence
                      </a>
                    ) : null}
                  </div>
                </div>
              </li>
            ))}
          </ol>
        ) : (
          <p className="recent-completions-empty">
            No tasks are complete yet. Finished work and its evidence will appear here.
          </p>
        )}
      </section>

      <section aria-labelledby="question-title">
        <div className="section-heading">
          <h2 id="question-title">The question behind the plan</h2>
          <p>{plan.project.researchQuestion}</p>
        </div>
      </section>

      <Timeline weeks={timelineWeeks} timezone={plan.project.timezone} />
    </div>
  );
}
