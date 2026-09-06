import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  CreateGateForm,
  CreateTaskForm,
  GateForm,
  ReflectionForm,
  TaskForm,
  WeekClosureForm,
  WeekDetailsForm,
} from "@/components/editor-forms";
import { StatusLabel } from "@/components/status-label";
import { requireOwner } from "@/lib/auth";
import { loadPlanFromSupabase } from "@/lib/data";
import { formatDateRange, weekCanClose, weekIsReady } from "@/lib/domain";

type EditWeekPageProps = { params: Promise<{ number: string }> };

export async function generateMetadata({ params }: EditWeekPageProps): Promise<Metadata> {
  const { number } = await params;
  return { title: `Edit week ${number}` };
}

export default async function EditWeekPage({ params }: EditWeekPageProps) {
  const { number } = await params;
  const { supabase } = await requireOwner();
  const plan = await loadPlanFromSupabase(supabase);
  const week = plan.weeks.find((candidate) => candidate.number === Number(number));
  if (!week) notFound();
  const ready = weekIsReady(plan.weeks, week.number);

  return (
    <div className="shell page-shell editor-page">
      <nav aria-label="Breadcrumb" className="breadcrumbs">
        <Link href="/edit">Update</Link>
        <span aria-hidden="true">/</span>
        <span aria-current="page">Week {week.number}</span>
      </nav>
      <header className="edit-week-header">
        <div>
          <div className="week-kicker">
            <span>{formatDateRange(week.startDate, week.endDate)}</span>
            <span>Record version {week.version}</span>
          </div>
          <h1>Week {week.number}: {week.title}</h1>
        </div>
        <div className="week-status-stack">
          <StatusLabel status={week.state} />
          <StatusLabel status={ready ? "ready" : "not_ready"} />
          <Link className="text-link" href={`/weeks/${week.number}`}>Public view</Link>
        </div>
      </header>

      {week.state === "closed" ? (
        <aside className="prerequisite-warning">
          This week is closed. Reopen it with a reason before changing its content or states.
        </aside>
      ) : null}

      {week.state !== "closed" ? (
        <>
          <section className="editor-section" aria-labelledby="week-details-title">
            <h2 id="week-details-title">Week details</h2>
            <WeekDetailsForm week={week} />
          </section>

          <section className="editor-section" aria-labelledby="tasks-editor-title">
            <div className="section-heading compact">
              <h2 id="tasks-editor-title">Tasks</h2>
              <p>Evidence links must be public-safe http or https URLs.</p>
            </div>
            <div className="editor-record-list">
              {week.tasks.map((task) => (
                <TaskForm key={task.id} task={task} weekNumber={week.number} />
              ))}
            </div>
            <CreateTaskForm week={week} />
          </section>

          <section className="editor-section" aria-labelledby="gates-editor-title">
            <div className="section-heading compact">
              <h2 id="gates-editor-title">Advancement gates</h2>
              <p>A met gate needs evidence. A waived gate needs a durable reason.</p>
            </div>
            <div className="editor-record-list">
              {week.gates.map((gate) => (
                <GateForm gate={gate} key={gate.id} weekNumber={week.number} />
              ))}
            </div>
            <CreateGateForm week={week} />
          </section>
        </>
      ) : (
        <section className="editor-section" aria-labelledby="closed-reflection-title">
          <div className="section-heading compact">
            <h2 id="closed-reflection-title">Closed-week reflection</h2>
            <p>Add context without changing the locked plan, tasks, or gate decisions.</p>
          </div>
          <ReflectionForm week={week} />
        </section>
      )}

      <section className="editor-section closure-section" aria-labelledby="closure-title">
        <div>
          <h2 id="closure-title">{week.state === "closed" ? "Reopen this week" : "Close this week"}</h2>
          <p>
            {week.state === "closed"
              ? "Reopening is permanent in the activity log and requires a reason."
              : weekCanClose(week)
                ? "All required tasks and gates are resolved."
                : "Required work remains unresolved."}
          </p>
        </div>
        <WeekClosureForm week={week} />
      </section>
    </div>
  );
}
