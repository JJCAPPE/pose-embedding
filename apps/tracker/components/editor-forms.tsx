"use client";

import {
  DownloadOutlined,
  EditOutlined,
  LockOutlined,
  LogoutOutlined,
  PlusOutlined,
  RightOutlined,
} from "@ant-design/icons";
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Collapse,
  Empty,
  Form,
  Input,
  Listy,
  Progress,
  Select,
  Statistic,
} from "antd";
import Link from "next/link";
import { useActionState, useState } from "react";
import {
  closeWeekAction,
  createGateAction,
  createTaskAction,
  logoutAction,
  reopenWeekAction,
  updateGateAction,
  updateReflectionAction,
  updateTaskAction,
  updateWeekAction,
} from "@/app/actions";
import { ActionFeedback } from "@/components/action-feedback";
import { InternalLinkButton } from "@/components/internal-link-button";
import { PriorityBrief } from "@/components/priority-brief";
import { SourceManagement } from "@/components/source-editor-forms";
import { StatusLabel } from "@/components/status-label";
import { SubmitButton } from "@/components/submit-button";
import { initialActionState } from "@/lib/action-state";
import { formatDateRange, weekCanClose, weekIsReady, weekProgress } from "@/lib/domain";
import type { Gate, Source, Task, Week } from "@/lib/schema";

const FormItem = Form.Item;
const TextArea = Input.TextArea;

const WEEK_STATE_OPTIONS = [
  { label: "Planned", value: "planned" },
  { label: "Active", value: "active" },
  { label: "Blocked", value: "blocked" },
];

const TASK_STATE_OPTIONS = [
  { label: "To do", value: "todo" },
  { label: "In progress", value: "in_progress" },
  { label: "Blocked", value: "blocked" },
  { label: "Done", value: "done" },
  { label: "Skipped", value: "skipped" },
];

const GATE_STATE_OPTIONS = [
  { label: "Pending", value: "pending" },
  { label: "Met", value: "met" },
  { label: "Waived", value: "waived" },
];

type DashboardProgress = {
  completedRequiredTasks: number;
  decidedRequiredGates: number;
  percent: number;
  requiredGates: number;
  requiredTasks: number;
};

function NativeSelect({
  defaultValue,
  id,
  name,
  options,
}: {
  defaultValue: string;
  id: string;
  name: string;
  options: { label: string; value: string }[];
}) {
  const [value, setValue] = useState(defaultValue);
  return (
    <>
      <Select id={id} onChange={setValue} options={options} value={value} />
      <input name={name} type="hidden" value={value} />
    </>
  );
}

export function EditDashboard({
  closedWeeks,
  progress,
  sources,
  weekSourcesCount,
  weeks,
}: {
  closedWeeks: number;
  progress: DashboardProgress;
  sources: Source[];
  weekSourcesCount: number;
  weeks: Week[];
}) {
  const nextWeek = weeks.find((week) => week.state !== "closed") ?? weeks.at(-1)!;
  const nextTask =
    nextWeek.tasks.find((task) => task.required && task.state !== "done") ??
    nextWeek.tasks.find((task) => task.state !== "done" && task.state !== "skipped");
  const pendingGates = nextWeek.gates.filter(
    (gate) => gate.required && gate.state === "pending",
  );

  return (
    <div className="shell page-shell editor-page owner-editor-page">
      <header className="editor-header owner-editor-header">
        <div>
          <h1>Keep the study record current.</h1>
          <p>
            Update evidence as work happens, make each decision explicit, and close a week only
            when its required record is complete.
          </p>
        </div>
        <div className="editor-header-actions">
          <Button href="/api/export/private" icon={<DownloadOutlined />}>
            Export archive
          </Button>
          <form action={logoutAction}>
            <Button htmlType="submit" icon={<LogoutOutlined />}>
              Sign out
            </Button>
          </form>
        </div>
      </header>

      <PriorityBrief
        actionHref={`/edit/weeks/${nextWeek.number}`}
        actionLabel={`Update Week ${nextWeek.number}`}
        decision={
          pendingGates.length > 0 ? (
            <ol className="priority-list">
              {pendingGates.map((gate) => <li key={gate.id}>{gate.criterion}</li>)}
            </ol>
          ) : (
            <p>No required gate decision is waiting in this week.</p>
          )
        }
        deliverable={<p>{nextWeek.deliverable}</p>}
        nextDescription={
          nextTask
            ? `Week ${nextWeek.number}: ${nextWeek.title}. Evidence needed: ${nextTask.expectedOutput}`
            : `Review Week ${nextWeek.number} and confirm its record is ready to close.`
        }
        nextTitle={nextTask?.title ?? `Review Week ${nextWeek.number}`}
        progress={{
          label: `${progress.completedRequiredTasks} of ${progress.requiredTasks} required tasks complete`,
          percent: progress.percent,
        }}
      />

      <section className="editor-summary" aria-label="Progress summary">
        <Card>
          <Statistic suffix="%" title="Required work complete" value={progress.percent} />
        </Card>
        <Card>
          <Statistic
            suffix={`/${progress.requiredGates}`}
            title="Required gates decided"
            value={progress.decidedRequiredGates}
          />
        </Card>
        <Card>
          <Statistic suffix={`/${weeks.length}`} title="Weeks closed" value={closedWeeks} />
        </Card>
      </section>

      <section className="owner-primary-section" aria-labelledby="edit-weeks-title">
        <div className="section-heading compact">
          <div>
            <h2 id="edit-weeks-title">Weekly records</h2>
            <p>Choose a week to update its work, evidence, decisions, hours, or reflection.</p>
          </div>
        </div>
        {weeks.length > 0 ? (
          <div role="list">
            <Listy
          className="editor-week-list editor-week-list-ant"
          itemRender={(week: Week) => {
            const weekStatus = weekProgress(week);
            return (
              <div role="listitem">
                <Link className="editor-week-link" href={`/edit/weeks/${week.number}`}>
                  <span className="editor-week-number">{String(week.number).padStart(2, "0")}</span>
                  <span className="editor-week-copy">
                    <strong>{week.title}</strong>
                    <small>{formatDateRange(week.startDate, week.endDate)}</small>
                    <span className="week-progress-row">
                      <Progress
                        aria-label={`${weekStatus.completed} of ${weekStatus.required} required tasks complete`}
                        percent={weekStatus.percent}
                        showInfo={false}
                        size="small"
                      />
                      <small>{weekStatus.completed}/{weekStatus.required} required tasks</small>
                    </span>
                  </span>
                  <span className="editor-week-status">
                    <StatusLabel status={week.state} />
                    <StatusLabel status={weekIsReady(weeks, week.number) ? "ready" : "not_ready"} />
                    <small>{weekCanClose(week) ? "Ready to close" : "Open requirements"}</small>
                  </span>
                  <RightOutlined aria-hidden="true" className="editor-week-arrow" />
                </Link>
              </div>
            );
          }}
              items={weeks}
              rowKey="id"
            />
          </div>
        ) : (
          <Empty description="No weekly records" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        )}
      </section>

      <section className="owner-supporting-section" aria-labelledby="source-management-title">
        <div className="section-heading compact">
          <div>
            <h2 id="source-management-title">Sources and weekly reading</h2>
            <p>Open these supporting records only when literature metadata or reading links change.</p>
          </div>
        </div>
        <SourceManagement
          sources={sources}
          weekSourcesCount={weekSourcesCount}
          weeks={weeks.map(({ id, number, state, title }) => ({ id, number, state, title }))}
        />
      </section>
    </div>
  );
}

export function EditWeekWorkspace({ ready, week }: { ready: boolean; week: Week }) {
  const progress = weekProgress(week);
  const nextTask =
    week.tasks.find((task) => task.required && task.state !== "done") ??
    week.tasks.find((task) => task.state !== "done" && task.state !== "skipped");
  const pendingGates = week.gates.filter((gate) => gate.required && gate.state === "pending");
  const firstPendingGate = pendingGates[0];
  const closed = week.state === "closed";
  const canClose = weekCanClose(week);
  const nextTitle = closed
    ? "Review the completed record"
    : nextTask?.title ?? firstPendingGate?.criterion ?? "Close the week";
  const nextDescription = closed
    ? "The plan, tasks, and decisions are read-only. Add reflection context or reopen with a recorded reason."
    : nextTask
      ? `Evidence needed: ${nextTask.expectedOutput}`
      : firstPendingGate
        ? "Record evidence for a met decision or a durable reason for a waiver."
        : "All required work is resolved. Review the record once, then close the week.";
  const actionHref = closed
    ? `/weeks/${week.number}`
    : nextTask
      ? `#task-${nextTask.id}`
      : firstPendingGate
        ? `#gate-${firstPendingGate.id}`
        : "#closure-title";

  return (
    <div className="shell page-shell editor-page owner-edit-week">
      <nav aria-label="Breadcrumb" className="breadcrumbs">
        <Link href="/edit">Update</Link>
        <span aria-hidden="true">/</span>
        <span aria-current="page">Week {week.number}</span>
      </nav>

      <header className="edit-week-header owner-editor-header">
        <div>
          <div className="week-kicker">
            <span>{formatDateRange(week.startDate, week.endDate)}</span>
            <span>Record version {week.version}</span>
          </div>
          <h1>Week {week.number}: {week.title}</h1>
          <p>{week.objective}</p>
        </div>
        <div className="week-status-stack">
          <StatusLabel status={week.state} />
          <StatusLabel status={ready ? "ready" : "not_ready"} />
          <InternalLinkButton
            href={`/weeks/${week.number}`}
            icon={<RightOutlined />}
            iconPlacement="end"
          >
            Public view
          </InternalLinkButton>
        </div>
      </header>

      <PriorityBrief
        actionHref={actionHref}
        actionLabel={
          closed ? "Open public view" : nextTask ? "Update this task" : firstPendingGate ? "Record decision" : "Review closure"
        }
        decision={
          pendingGates.length > 0 ? (
            <ol className="priority-list">
              {pendingGates.map((gate) => <li key={gate.id}>{gate.criterion}</li>)}
            </ol>
          ) : (
            <p>{closed ? "Every required gate was resolved before closure." : "No required gate decision remains."}</p>
          )
        }
        deliverable={<p>{week.deliverable}</p>}
        nextDescription={nextDescription}
        nextTitle={nextTitle}
        progress={{
          label: `${progress.completed} of ${progress.required} required tasks complete`,
          percent: progress.percent,
        }}
      />

      {closed ? (
        <Alert
          className="prerequisite-warning"
          description="Reopen it with a reason before changing its plan, task states, or gate decisions. Reflection remains available below."
          title="This week is closed and read-only."
          showIcon
          type="info"
        />
      ) : null}

      {!closed ? (
        <>
          <section className="editor-section" aria-labelledby="week-details-title">
            <Collapse
              className="editor-section-collapse"
              items={[
                {
                  children: <WeekDetailsForm week={week} />,
                  key: "week-details",
                  label: (
                    <span className="collapse-section-label">
                      <EditOutlined />
                      <span>
                        <strong id="week-details-title">Week details</strong>
                        <small>Objective, deliverable, risks, time, and working state</small>
                      </span>
                    </span>
                  ),
                },
              ]}
            />
          </section>

          <section className="editor-section" aria-labelledby="tasks-editor-title">
            <div className="section-heading compact">
              <div>
                <h2 id="tasks-editor-title">Tasks</h2>
                <p>Open one task at a time. Evidence links must be public-safe http or https URLs.</p>
              </div>
            </div>
            <div className="editor-record-list">
              {week.tasks.length > 0 ? (
                week.tasks.map((task) => (
                  <TaskForm
                    defaultOpen={task.id === nextTask?.id}
                    key={task.id}
                    task={task}
                    weekNumber={week.number}
                  />
                ))
              ) : (
                <Empty description="No tasks yet" image={Empty.PRESENTED_IMAGE_SIMPLE} />
              )}
            </div>
            <CreateTaskForm week={week} />
          </section>

          <section className="editor-section" aria-labelledby="gates-editor-title">
            <div className="section-heading compact">
              <div>
                <h2 id="gates-editor-title">Advancement decisions</h2>
                <p>A met gate needs evidence. A waived gate needs a durable reason.</p>
              </div>
            </div>
            <div className="editor-record-list">
              {week.gates.length > 0 ? (
                week.gates.map((gate) => (
                  <GateForm
                    defaultOpen={gate.id === firstPendingGate?.id && !nextTask}
                    gate={gate}
                    key={gate.id}
                    weekNumber={week.number}
                  />
                ))
              ) : (
                <Empty description="No advancement gates yet" image={Empty.PRESENTED_IMAGE_SIMPLE} />
              )}
            </div>
            <CreateGateForm week={week} />
          </section>
        </>
      ) : (
        <ClosedWeekRecords week={week} />
      )}

      {closed ? (
        <section className="editor-section" aria-labelledby="closed-reflection-title">
          <div className="section-heading compact">
            <div>
              <h2 id="closed-reflection-title">Closed-week reflection</h2>
              <p>Add context without changing the locked plan, tasks, or gate decisions.</p>
            </div>
          </div>
          <Card>
            <ReflectionForm week={week} />
          </Card>
        </section>
      ) : null}

      <section className="editor-section closure-section" aria-labelledby="closure-title">
        <Card className="closure-card">
          <div className="closure-copy">
            <LockOutlined aria-hidden="true" />
            <div>
              <h2 id="closure-title">{closed ? "Reopen this week" : "Close this week"}</h2>
              <p>
                {closed
                  ? "Reopening is permanent in the activity log and requires a reason."
                  : canClose
                    ? "All required tasks and decisions are resolved."
                    : "Complete required tasks and resolve required decisions before closing."}
              </p>
            </div>
          </div>
          <WeekClosureForm week={week} />
        </Card>
      </section>
    </div>
  );
}

function ClosedWeekRecords({ week }: { week: Week }) {
  return (
    <section className="closed-records" aria-label="Closed week record">
      <Card title="Tasks at closure">
        {week.tasks.length > 0 ? (
          <div role="list">
            <Listy
          itemRender={(task: Task) => (
            <div role="listitem">
              <div className="closed-record-row">
                <div>
                  <strong>{task.title}</strong>
                  <p>{task.expectedOutput}</p>
                </div>
                <StatusLabel status={task.state} />
              </div>
            </div>
          )}
              items={week.tasks}
              rowKey="id"
            />
          </div>
        ) : (
          <Empty description="No tasks were recorded." image={Empty.PRESENTED_IMAGE_SIMPLE} />
        )}
      </Card>
      <Card title="Decisions at closure">
        {week.gates.length > 0 ? (
          <div role="list">
            <Listy
          itemRender={(gate: Gate) => (
            <div role="listitem">
              <div className="closed-record-row">
                <div>
                  <strong>{gate.criterion}</strong>
                  {gate.evidence ? <p>Evidence: {gate.evidence}</p> : null}
                  {gate.waiverReason ? <p>Waiver: {gate.waiverReason}</p> : null}
                </div>
                <StatusLabel status={gate.state} />
              </div>
            </div>
          )}
              items={week.gates}
              rowKey="id"
            />
          </div>
        ) : (
          <Empty
            description="No advancement decisions were recorded."
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </Card>
    </section>
  );
}

export function WeekDetailsForm({ week }: { week: Week }) {
  const [state, action] = useActionState(updateWeekAction, initialActionState);
  return (
    <form action={action} className="editor-form">
      <input name="id" type="hidden" value={week.id} />
      <input name="number" type="hidden" value={week.number} />
      <input name="version" type="hidden" value={week.version} />
      <Form component={false} layout="vertical">
        <div className="field-grid">
          <FormItem className="field" htmlFor="week-title" label="Title" required>
            <Input defaultValue={week.title} id="week-title" name="title" required />
          </FormItem>
          <FormItem className="field" htmlFor="week-phase" label="Phase" required>
            <Input defaultValue={week.phase} id="week-phase" name="phase" required />
          </FormItem>
          <FormItem className="field span-two" htmlFor="week-objective" label="Objective" required>
            <TextArea defaultValue={week.objective} id="week-objective" name="objective" required rows={4} />
          </FormItem>
          <FormItem className="field span-two" htmlFor="week-deliverable" label="Deliverable" required>
            <TextArea defaultValue={week.deliverable} id="week-deliverable" name="deliverable" required rows={3} />
          </FormItem>
          <FormItem
            className="field span-two"
            extra="Use one risk per line."
            htmlFor="week-risks"
            label="Risks"
          >
            <TextArea defaultValue={week.risks.join("\n")} id="week-risks" name="risks" rows={4} />
          </FormItem>
          <FormItem className="field span-two" htmlFor="week-advisor" label="Advisor prompt" required>
            <TextArea defaultValue={week.advisorPrompt} id="week-advisor" name="advisorPrompt" required rows={3} />
          </FormItem>
          <FormItem className="field span-two" htmlFor="week-reflection" label="Reflection">
            <TextArea defaultValue={week.reflection} id="week-reflection" name="reflection" rows={5} />
          </FormItem>
          <FormItem className="field" htmlFor="week-planned" label="Planned minutes">
            <Input defaultValue={week.plannedMinutes} id="week-planned" min="0" name="plannedMinutes" type="number" />
          </FormItem>
          <FormItem className="field" htmlFor="week-actual" label="Actual minutes">
            <Input defaultValue={week.actualMinutes} id="week-actual" min="0" name="actualMinutes" type="number" />
          </FormItem>
          <FormItem className="field" htmlFor="week-state" label="Working state">
            <NativeSelect
              defaultValue={week.state === "closed" ? "active" : week.state}
              id="week-state"
              name="state"
              options={WEEK_STATE_OPTIONS}
            />
          </FormItem>
        </div>
      </Form>
      <div className="form-footer">
        <ActionFeedback state={state} />
        <SubmitButton>Save week</SubmitButton>
      </div>
    </form>
  );
}

export function TaskForm({
  defaultOpen = false,
  task,
  weekNumber,
}: {
  defaultOpen?: boolean;
  task: Task;
  weekNumber: number;
}) {
  const [state, action] = useActionState(updateTaskAction, initialActionState);
  const fieldPrefix = `task-${task.id}`;
  return (
    <div id={fieldPrefix}>
      <Collapse
        className="record-collapse"
        defaultActiveKey={defaultOpen ? [task.id] : []}
        items={[
          {
            children: (
              <form action={action} className="record-form">
                <input name="id" type="hidden" value={task.id} />
                <input name="weekNumber" type="hidden" value={weekNumber} />
                <input name="version" type="hidden" value={task.version} />
                <Form component={false} layout="vertical">
                  <div className="field-grid compact-fields">
                    <FormItem className="field span-two">
                      <Checkbox defaultChecked={task.required} name="required" value="on">
                        Required for week closure
                      </Checkbox>
                    </FormItem>
                    <FormItem className="field span-two" htmlFor={`${fieldPrefix}-title`} label="Title" required>
                      <Input defaultValue={task.title} id={`${fieldPrefix}-title`} name="title" required />
                    </FormItem>
                    <FormItem
                      className="field"
                      extra="Order values must be unique within the week."
                      htmlFor={`${fieldPrefix}-position`}
                      label="Order"
                      required
                    >
                      <Input defaultValue={task.position} id={`${fieldPrefix}-position`} min="1" name="position" required type="number" />
                    </FormItem>
                    <FormItem className="field" htmlFor={`${fieldPrefix}-estimate`} label="Estimated minutes" required>
                      <Input defaultValue={task.estimateMinutes} id={`${fieldPrefix}-estimate`} min="0" name="estimateMinutes" required type="number" />
                    </FormItem>
                    <FormItem className="field span-two" htmlFor={`${fieldPrefix}-details`} label="Details">
                      <TextArea defaultValue={task.details} id={`${fieldPrefix}-details`} name="details" rows={3} />
                    </FormItem>
                    <FormItem className="field span-two" htmlFor={`${fieldPrefix}-output`} label="Expected evidence" required>
                      <TextArea defaultValue={task.expectedOutput} id={`${fieldPrefix}-output`} name="expectedOutput" required rows={3} />
                    </FormItem>
                    <FormItem className="field" htmlFor={`${fieldPrefix}-state`} label="State">
                      <NativeSelect defaultValue={task.state} id={`${fieldPrefix}-state`} name="state" options={TASK_STATE_OPTIONS} />
                    </FormItem>
                    <FormItem className="field" htmlFor={`${fieldPrefix}-evidence`} label="Evidence URL">
                      <Input defaultValue={task.evidenceUrl ?? ""} id={`${fieldPrefix}-evidence`} inputMode="url" name="evidenceUrl" type="url" />
                    </FormItem>
                    <FormItem
                      className="field span-two"
                      htmlFor={`${fieldPrefix}-note`}
                      label="Completion note or requirement-change reason"
                    >
                      <TextArea defaultValue={task.completionNote} id={`${fieldPrefix}-note`} name="completionNote" rows={3} />
                    </FormItem>
                  </div>
                </Form>
                <div className="form-footer">
                  <ActionFeedback state={state} />
                  <SubmitButton>Save task</SubmitButton>
                </div>
              </form>
            ),
            extra: <StatusLabel status={task.state} />,
            key: task.id,
            label: (
              <span className="record-collapse-label">
                <small>Task {task.position}</small>
                <strong>{task.title}</strong>
              </span>
            ),
          },
        ]}
      />
    </div>
  );
}

export function GateForm({
  defaultOpen = false,
  gate,
  weekNumber,
}: {
  defaultOpen?: boolean;
  gate: Gate;
  weekNumber: number;
}) {
  const [state, action] = useActionState(updateGateAction, initialActionState);
  const fieldPrefix = `gate-${gate.id}`;
  return (
    <div id={fieldPrefix}>
      <Collapse
        className="record-collapse gate-form"
        defaultActiveKey={defaultOpen ? [gate.id] : []}
        items={[
          {
            children: (
              <form action={action} className="record-form gate-form">
                <input name="id" type="hidden" value={gate.id} />
                <input name="weekNumber" type="hidden" value={weekNumber} />
                <input name="version" type="hidden" value={gate.version} />
                <Form component={false} layout="vertical">
                  <div className="field-grid compact-fields">
                    <FormItem className="field span-two">
                      <Checkbox defaultChecked={gate.required} name="required" value="on">
                        Required for week closure
                      </Checkbox>
                    </FormItem>
                    <FormItem className="field span-two" htmlFor={`${fieldPrefix}-criterion`} label="Criterion" required>
                      <TextArea defaultValue={gate.criterion} id={`${fieldPrefix}-criterion`} name="criterion" required rows={3} />
                    </FormItem>
                    <FormItem
                      className="field"
                      extra="Order values must be unique within the week."
                      htmlFor={`${fieldPrefix}-position`}
                      label="Order"
                      required
                    >
                      <Input defaultValue={gate.position} id={`${fieldPrefix}-position`} min="1" name="position" required type="number" />
                    </FormItem>
                    <FormItem className="field" htmlFor={`${fieldPrefix}-state`} label="Decision">
                      <NativeSelect defaultValue={gate.state} id={`${fieldPrefix}-state`} name="state" options={GATE_STATE_OPTIONS} />
                    </FormItem>
                    <FormItem className="field span-two" htmlFor={`${fieldPrefix}-evidence`} label="Evidence">
                      <TextArea defaultValue={gate.evidence} id={`${fieldPrefix}-evidence`} name="evidence" rows={3} />
                    </FormItem>
                    <FormItem className="field span-two" htmlFor={`${fieldPrefix}-waiver`} label="Waiver reason">
                      <TextArea defaultValue={gate.waiverReason} id={`${fieldPrefix}-waiver`} name="waiverReason" rows={3} />
                    </FormItem>
                  </div>
                </Form>
                <div className="form-footer">
                  <ActionFeedback state={state} />
                  <SubmitButton>Save decision</SubmitButton>
                </div>
              </form>
            ),
            extra: <StatusLabel status={gate.state} />,
            key: gate.id,
            label: (
              <span className="record-collapse-label">
                <small>Decision {gate.position}</small>
                <strong>{gate.criterion}</strong>
              </span>
            ),
          },
        ]}
      />
    </div>
  );
}

export function CreateTaskForm({ week }: { week: Week }) {
  const [state, action] = useActionState(createTaskAction, initialActionState);
  return (
    <Collapse
      className="create-record"
      items={[
        {
          children: (
            <form action={action} className="record-form">
              <input name="weekId" type="hidden" value={week.id} />
              <input name="weekNumber" type="hidden" value={week.number} />
              <Form component={false} layout="vertical">
                <div className="field-grid compact-fields">
                  <FormItem className="field" htmlFor="new-task-title" label="Title" required>
                    <Input id="new-task-title" name="title" required />
                  </FormItem>
                  <FormItem className="field" htmlFor="new-task-estimate" label="Estimated minutes">
                    <Input defaultValue="60" id="new-task-estimate" min="0" name="estimateMinutes" type="number" />
                  </FormItem>
                  <FormItem className="field span-two" htmlFor="new-task-details" label="Details">
                    <TextArea id="new-task-details" name="details" rows={3} />
                  </FormItem>
                  <FormItem className="field span-two" htmlFor="new-task-output" label="Expected evidence" required>
                    <TextArea id="new-task-output" name="expectedOutput" required rows={3} />
                  </FormItem>
                  <FormItem className="field span-two">
                    <Checkbox defaultChecked name="required" value="on">
                      Required for week closure
                    </Checkbox>
                  </FormItem>
                </div>
              </Form>
              <div className="form-footer">
                <ActionFeedback state={state} />
                <SubmitButton pendingLabel="Adding">Add task</SubmitButton>
              </div>
            </form>
          ),
          key: "create-task",
          label: <span className="create-record-label"><PlusOutlined /> Add a task</span>,
        },
      ]}
    />
  );
}

export function CreateGateForm({ week }: { week: Week }) {
  const [state, action] = useActionState(createGateAction, initialActionState);
  return (
    <Collapse
      className="create-record"
      items={[
        {
          children: (
            <form action={action} className="record-form gate-form">
              <input name="weekId" type="hidden" value={week.id} />
              <input name="weekNumber" type="hidden" value={week.number} />
              <Form component={false} layout="vertical">
                <div className="field-grid compact-fields">
                  <FormItem className="field span-two" htmlFor="new-gate-criterion" label="Criterion" required>
                    <TextArea id="new-gate-criterion" name="criterion" required rows={3} />
                  </FormItem>
                  <FormItem className="field span-two">
                    <Checkbox defaultChecked name="required" value="on">
                      Required for week closure
                    </Checkbox>
                  </FormItem>
                </div>
              </Form>
              <div className="form-footer">
                <ActionFeedback state={state} />
                <SubmitButton pendingLabel="Adding">Add decision</SubmitButton>
              </div>
            </form>
          ),
          key: "create-gate",
          label: <span className="create-record-label"><PlusOutlined /> Add a decision</span>,
        },
      ]}
    />
  );
}

export function WeekClosureForm({ week }: { week: Week }) {
  const action = week.state === "closed" ? reopenWeekAction : closeWeekAction;
  const [state, formAction] = useActionState(action, initialActionState);
  const canSubmit = week.state === "closed" || weekCanClose(week);
  return (
    <form action={formAction} className="closure-form">
      <input name="id" type="hidden" value={week.id} />
      <input name="number" type="hidden" value={week.number} />
      <input name="version" type="hidden" value={week.version} />
      {week.state === "closed" ? (
        <Form component={false} layout="vertical">
          <FormItem className="field" htmlFor="reopen-reason" label="Reason for reopening" required>
            <TextArea id="reopen-reason" name="reason" required rows={3} />
          </FormItem>
        </Form>
      ) : (
        <p>Closing unlocks the next week and freezes this week&apos;s plan and decisions.</p>
      )}
      <div className="form-footer">
        <ActionFeedback state={state} />
        <SubmitButton
          className={week.state === "closed" ? "button secondary compact-button" : "button primary compact-button"}
          disabled={!canSubmit}
        >
          {week.state === "closed" ? "Reopen week" : "Close week"}
        </SubmitButton>
      </div>
    </form>
  );
}

export function ReflectionForm({ week }: { week: Week }) {
  const [state, action] = useActionState(updateReflectionAction, initialActionState);
  return (
    <form action={action} className="editor-form">
      <input name="id" type="hidden" value={week.id} />
      <input name="number" type="hidden" value={week.number} />
      <input name="version" type="hidden" value={week.version} />
      <Form component={false} layout="vertical">
        <FormItem
          className="field"
          extra="Reflection remains editable while the plan itself is closed."
          htmlFor="closed-reflection"
          label="Reflection"
        >
          <TextArea defaultValue={week.reflection} id="closed-reflection" name="reflection" rows={6} />
        </FormItem>
      </Form>
      <div className="form-footer">
        <ActionFeedback state={state} />
        <SubmitButton>Save reflection</SubmitButton>
      </div>
    </form>
  );
}
