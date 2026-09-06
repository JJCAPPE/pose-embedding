import type { Metadata } from "next";
import Link from "next/link";
import { logoutAction } from "@/app/actions";
import {
  CreateSourceForm,
  LinkSourceForm,
  SourceForm,
} from "@/components/source-editor-forms";
import { StatusLabel } from "@/components/status-label";
import { requireOwner } from "@/lib/auth";
import { loadPlanFromSupabase } from "@/lib/data";
import { formatDateRange, projectProgress, weekCanClose, weekIsReady } from "@/lib/domain";

export const metadata: Metadata = { title: "Update progress" };
export default async function EditDashboardPage() {
  const { supabase } = await requireOwner();
  const plan = await loadPlanFromSupabase(supabase);
  const progress = projectProgress(plan);

  return (
    <div className="shell page-shell editor-page">
      <header className="editor-header">
        <div>
          <p className="eyebrow">Private workspace</p>
          <h1>Update the record.</h1>
          <p>
            Changes publish to the advisor view. Every update is checked against its current version.
          </p>
        </div>
        <div className="editor-header-actions">
          <a className="button secondary compact-button" href="/api/export/private">
            Export archive
          </a>
          <form action={logoutAction}>
            <button className="button secondary compact-button" type="submit">Sign out</button>
          </form>
        </div>
      </header>

      <section className="editor-summary" aria-label="Progress summary">
        <div>
          <strong>{progress.percent}%</strong>
          <span>required tasks complete</span>
        </div>
        <div>
          <strong>{progress.decidedRequiredGates}/{progress.requiredGates}</strong>
          <span>required gates decided</span>
        </div>
        <div>
          <strong>{plan.weeks.filter((week) => week.state === "closed").length}/14</strong>
          <span>weeks closed</span>
        </div>
      </section>

      <section aria-labelledby="edit-weeks-title">
        <div className="section-heading compact">
          <h2 id="edit-weeks-title">Weekly records</h2>
          <p>Open one week to update its hours, tasks, evidence, gates, and reflection.</p>
        </div>
        <ol className="editor-week-list">
          {plan.weeks.map((week) => (
            <li key={week.id}>
              <Link href={`/edit/weeks/${week.number}`}>
                <span className="editor-week-number">{String(week.number).padStart(2, "0")}</span>
                <span className="editor-week-copy">
                  <strong>{week.title}</strong>
                  <small>{formatDateRange(week.startDate, week.endDate)}</small>
                </span>
                <span className="editor-week-status">
                  <StatusLabel status={week.state} />
                  <StatusLabel status={weekIsReady(plan.weeks, week.number) ? "ready" : "not_ready"} />
                  <small>{weekCanClose(week) ? "Can close" : "Open requirements"}</small>
                </span>
              </Link>
            </li>
          ))}
        </ol>
      </section>

      <section className="editor-section" aria-labelledby="edit-sources-title">
        <div className="section-heading compact">
          <h2 id="edit-sources-title">Source ledger</h2>
          <p>Edit verified literature metadata or add a public-safe source.</p>
        </div>
        <div className="editor-record-list">
          {plan.sources.map((source) => <SourceForm key={source.id} source={source} />)}
        </div>
        <CreateSourceForm />
      </section>

      <section className="editor-section" aria-labelledby="link-source-title">
        <div className="section-heading compact">
          <h2 id="link-source-title">Weekly reading links</h2>
          <p>{plan.weekSources.length} links currently connect the source ledger to weekly work.</p>
        </div>
        <LinkSourceForm
          sources={plan.sources.map(({ id, title }) => ({ id, title }))}
          weeks={plan.weeks.map(({ id, number, state, title }) => ({ id, number, state, title }))}
        />
      </section>
    </div>
  );
}
