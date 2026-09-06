import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import Loading from "@/app/loading";
import { CurrentWeekMarker } from "@/components/current-week";
import { DataNotice } from "@/components/data-notice";
import { MarkdownText } from "@/components/markdown-text";
import { StatusLabel } from "@/components/status-label";
import { formatDateRange, weekCanClose, weekIsReady, weekProgress } from "@/lib/domain";
import { getRequestPublicPlan } from "@/lib/request-plan";

type WeekPageProps = { params: Promise<{ number: string }> };

function formatHours(minutes: number): string {
  const hours = minutes / 60;
  return `${Number.isInteger(hours) ? hours : hours.toFixed(1)}h`;
}

export async function generateStaticParams() {
  return Array.from({ length: 14 }, (_, index) => ({ number: String(index + 1) }));
}

export async function generateMetadata({ params }: WeekPageProps): Promise<Metadata> {
  const { number } = await params;
  const plan = await getRequestPublicPlan();
  const week = plan.weeks.find((candidate) => candidate.number === Number(number));
  if (!week) notFound();
  return { title: `Week ${week.number}: ${week.title}` };
}

export default function WeekPage(props: WeekPageProps) {
  return (
    <Suspense fallback={<Loading />}>
      <WeekPageContent {...props} />
    </Suspense>
  );
}

async function WeekPageContent({ params }: WeekPageProps) {
  const { number } = await params;
  const plan = await getRequestPublicPlan();
  const week = plan.weeks.find((candidate) => candidate.number === Number(number));
  if (!week) notFound();

  const progress = weekProgress(week);
  const ready = weekIsReady(plan.weeks, week.number);
  const previous = plan.weeks.find((candidate) => candidate.number === week.number - 1);
  const next = plan.weeks.find((candidate) => candidate.number === week.number + 1);
  const previousRequiredGates = previous?.gates.filter((gate) => gate.required) ?? [];
  const previousResolvedGates = previousRequiredGates.filter(
    (gate) => gate.state === "met" || gate.state === "waived",
  ).length;
  const sourceLinks = plan.weekSources
    .filter((link) => link.weekId === week.id)
    .map((link) => ({
      ...link,
      source: plan.sources.find((source) => source.id === link.sourceId),
    }))
    .filter((link) => link.source);

  return (
    <div className="shell page-shell">
      <DataNotice plan={plan} />
      <nav aria-label="Breadcrumb" className="breadcrumbs">
        <Link href="/">Plan</Link>
        <span aria-hidden="true">/</span>
        <span aria-current="page">Week {week.number}</span>
      </nav>

      <header className="week-header">
        <div>
          <div className="week-kicker">
            <span>{week.phase}</span>
            <span>{formatDateRange(week.startDate, week.endDate)}</span>
            <span>{formatHours(week.plannedMinutes)} planned</span>
            <span>{formatHours(week.actualMinutes)} actual</span>
          </div>
          <h1>Week {week.number}: {week.title}</h1>
          <p>{week.objective}</p>
        </div>
        <div className="week-status-stack">
          <StatusLabel status={week.state} />
          <StatusLabel status={ready ? "ready" : "not_ready"} />
          <CurrentWeekMarker
            startDate={week.startDate}
            endDate={week.endDate}
            timezone={plan.project.timezone}
          />
        </div>
      </header>

      <section className="start-prerequisites" aria-labelledby="prerequisites-title">
        <div>
          <p className="eyebrow">Start prerequisites</p>
          <h2 id="prerequisites-title">
            {previous ? `Close Week ${previous.number} before starting.` : "Begin from the locked protocol."}
          </h2>
          <p>
            {previous
              ? `${previousResolvedGates} of ${previousRequiredGates.length} required advancement gates are decided. This week becomes ready only when the previous week is closed.`
              : "There is no earlier weekly gate. Confirm the manual access actions and protocol approvals as part of Week 1."}
          </p>
        </div>
        <div className="prerequisite-status">
          {previous ? (
            <>
              <Link href={`/weeks/${previous.number}`}>
                Week {previous.number}: {previous.title}
              </Link>
              <StatusLabel status={previous.state} />
            </>
          ) : (
            <Link href="/protocol#manual-actions">Review manual actions</Link>
          )}
          <StatusLabel status={ready ? "ready" : "not_ready"} />
        </div>
      </section>

      <section className="deliverable-panel" aria-labelledby="deliverable-title">
        <div>
          <h2 id="deliverable-title">Finish line</h2>
          <p>{week.deliverable}</p>
        </div>
        <div className="week-completion-number">
          <span>{progress.percent}%</span>
          <small>{progress.completed}/{progress.required} required tasks</small>
        </div>
      </section>

      <div className="week-content-grid">
        <section aria-labelledby="tasks-title" className="week-main-column">
          <div className="section-heading compact">
            <h2 id="tasks-title">Work for the week</h2>
            <p>Each task names the evidence needed to count it as complete.</p>
          </div>
          <ol className="task-list">
            {week.tasks.map((task) => (
              <li className="task-item" key={task.id}>
                <div className="task-heading">
                  <span className="task-position">{task.position}</span>
                  <div>
                    <h3>{task.title}</h3>
                    <div className="task-meta">
                      <StatusLabel status={task.state} />
                      <span>{task.estimateMinutes / 60}h estimate</span>
                      <span>{task.required ? "Required" : "Optional"}</span>
                    </div>
                  </div>
                </div>
                <MarkdownText>{task.details}</MarkdownText>
                <div className="evidence-box">
                  <strong>Expected evidence</strong>
                  <p>{task.expectedOutput}</p>
                  {task.completionNote ? <p className="completion-note">{task.completionNote}</p> : null}
                  {task.evidenceUrl ? (
                    <a href={task.evidenceUrl} rel="noreferrer" target="_blank">Open evidence</a>
                  ) : null}
                </div>
              </li>
            ))}
          </ol>
        </section>

        <aside className="week-side-column">
          <section aria-labelledby="gates-title" className="side-section">
            <h2 id="gates-title">Advance when</h2>
            <ol className="gate-list">
              {week.gates.map((gate) => (
                <li key={gate.id}>
                  <StatusLabel status={gate.state} />
                  <p>{gate.criterion}</p>
                  {gate.evidence ? <small>Evidence: {gate.evidence}</small> : null}
                  {gate.waiverReason ? <small>Waiver: {gate.waiverReason}</small> : null}
                </li>
              ))}
            </ol>
            <p className="gate-verdict">
              {weekCanClose(week)
                ? "Every required condition is satisfied."
                : "Required conditions remain open."}
            </p>
          </section>

          <section aria-labelledby="risks-title" className="side-section">
            <h2 id="risks-title">Watch closely</h2>
            <ul className="risk-list">
              {week.risks.map((risk) => <li key={risk}>{risk}</li>)}
            </ul>
          </section>

          <section aria-labelledby="advisor-title" className="advisor-card">
            <h2 id="advisor-title">Advisor checkpoint</h2>
            <p>{week.advisorPrompt}</p>
          </section>

          {sourceLinks.length > 0 ? (
            <section aria-labelledby="reading-title" className="side-section">
              <h2 id="reading-title">Read before working</h2>
              <ul className="source-list">
                {sourceLinks.map(({ source, purpose, priority }) => (
                  <li key={source!.id}>
                    <a href={source!.canonicalUrl} rel="noreferrer" target="_blank">
                      {source!.title}
                    </a>
                    <small>{priority === "required" ? "Required" : "Recommended"}: {purpose}</small>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {week.reflection ? (
            <section aria-labelledby="reflection-title" className="side-section">
              <h2 id="reflection-title">Reflection</h2>
              <MarkdownText>{week.reflection}</MarkdownText>
            </section>
          ) : null}
        </aside>
      </div>

      <nav className="week-pagination" aria-label="Week navigation">
        {previous ? <Link href={`/weeks/${previous.number}`}>Previous: {previous.title}</Link> : <span />}
        {next ? <Link href={`/weeks/${next.number}`}>Next: {next.title}</Link> : <Link href="/">Return to plan</Link>}
      </nav>
    </div>
  );
}
