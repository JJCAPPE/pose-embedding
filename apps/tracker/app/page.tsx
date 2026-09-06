import Link from "next/link";
import { Suspense } from "react";
import Loading from "@/app/loading";
import { DataNotice } from "@/components/data-notice";
import { ProgressDial } from "@/components/progress-dial";
import { StatusLabel } from "@/components/status-label";
import { Timeline } from "@/components/timeline";
import { formatDateRange, projectProgress, weekIsReady } from "@/lib/domain";
import { getRequestPublicPlan } from "@/lib/request-plan";

export default function HomePage() {
  return (
    <Suspense fallback={<Loading />}>
      <HomePageContent />
    </Suspense>
  );
}

async function HomePageContent() {
  const plan = await getRequestPublicPlan();
  const progress = projectProgress(plan);
  const nextWeek = plan.weeks.find((week) => week.state !== "closed") ?? plan.weeks.at(-1)!;
  const nextRequiredGates = nextWeek.gates.filter(
    (gate) => gate.required && gate.state === "pending",
  );
  const recentCompletions = plan.weeks
    .flatMap((week) => week.tasks.map((task) => ({ task, week })))
    .filter(({ task }) => task.state === "done")
    .sort((a, b) => (b.task.completedAt ?? "").localeCompare(a.task.completedAt ?? ""))
    .slice(0, 4);

  return (
    <>
      <section className="hero shell">
        <div className="hero-copy">
          <p className="eyebrow">Fall 2026 research plan</p>
          <h1>From protocol lock to defensible evidence.</h1>
          <p className="hero-deck">
            Fourteen weeks of scoped work, explicit prerequisites, and evidence-backed decisions.
          </p>
          <div className="hero-actions">
            <Link className="button primary" href={`/weeks/${nextWeek.number}`}>
              Open next week
            </Link>
            <Link className="button secondary" href="/api/export?format=markdown">
              Export plan
            </Link>
          </div>
        </div>
        <div className="hero-progress" aria-label="Project progress summary">
          <ProgressDial percent={progress.percent} />
          <div>
            <p className="metric-label">Required work</p>
            <p className="metric-value">
              {progress.completedRequiredTasks} of {progress.requiredTasks}
            </p>
            <p className="muted">tasks complete across the full study</p>
          </div>
        </div>
      </section>

      <div className="shell">
        <DataNotice plan={plan} />
      </div>

      <section className="summary-band shell" aria-label="Project summary">
        <div className="question-block">
          <h2>The question</h2>
          <p>{plan.project.researchQuestion}</p>
        </div>
        <dl className="summary-metrics">
          <div>
            <dt>Study window</dt>
            <dd>{formatDateRange(plan.project.startDate, plan.project.endDate)}, 2026</dd>
          </div>
          <div>
            <dt>Core result due</dt>
            <dd>November 20</dd>
          </div>
          <div>
            <dt>Gate decisions</dt>
            <dd>
              {progress.decidedRequiredGates}/{progress.requiredGates}
            </dd>
          </div>
        </dl>
      </section>

      <section className="focus-grid shell" aria-labelledby="focus-title">
        <div className="focus-primary">
          <div className="section-heading compact">
            <h2 id="focus-title">Next decision</h2>
          </div>
          <div className="focus-title-row">
            <div>
              <p className="mono-label">
                Week {nextWeek.number}, {formatDateRange(nextWeek.startDate, nextWeek.endDate)}
              </p>
              <h3>{nextWeek.title}</h3>
            </div>
            <StatusLabel
              status={weekIsReady(plan.weeks, nextWeek.number) ? "ready" : "not_ready"}
            />
          </div>
          <p>{nextWeek.deliverable}</p>
          <Link className="text-link" href={`/weeks/${nextWeek.number}`}>
            Review tasks and prerequisites
          </Link>
        </div>
        <div className="focus-secondary">
          <h3>Required exit gates</h3>
          {nextRequiredGates.length > 0 ? (
            <ol className="compact-gates">
              {nextRequiredGates.map((gate) => (
                <li key={gate.id}>{gate.criterion}</li>
              ))}
            </ol>
          ) : (
            <p className="muted">Every required gate for this week is decided.</p>
          )}
        </div>
        <div className="focus-tertiary">
          <h3>Recent evidence</h3>
          {recentCompletions.length > 0 ? (
            <ul className="recent-list">
              {recentCompletions.map(({ task, week }) => (
                <li key={task.id}>
                  <span>{task.title}</span>
                  <Link href={`/weeks/${week.number}`}>Week {week.number}</Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">
              Completed tasks and their evidence links will appear here.
            </p>
          )}
        </div>
      </section>

      <div className="shell">
        <Timeline weeks={plan.weeks} timezone={plan.project.timezone} />
      </div>
    </>
  );
}
