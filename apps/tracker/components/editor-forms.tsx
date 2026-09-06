"use client";

import { useActionState } from "react";
import {
  closeWeekAction,
  createGateAction,
  createTaskAction,
  reopenWeekAction,
  updateReflectionAction,
  updateGateAction,
  updateTaskAction,
  updateWeekAction,
} from "@/app/actions";
import { ActionFeedback } from "@/components/action-feedback";
import { SubmitButton } from "@/components/submit-button";
import { initialActionState } from "@/lib/action-state";
import type { Gate, Task, Week } from "@/lib/schema";

export function WeekDetailsForm({ week }: { week: Week }) {
  const [state, action] = useActionState(updateWeekAction, initialActionState);
  return (
    <form action={action} className="editor-form">
      <input name="id" type="hidden" value={week.id} />
      <input name="number" type="hidden" value={week.number} />
      <input name="version" type="hidden" value={week.version} />
      <div className="field-grid">
        <div className="field">
          <label htmlFor="week-title">Title</label>
          <input defaultValue={week.title} id="week-title" name="title" required />
        </div>
        <div className="field">
          <label htmlFor="week-phase">Phase</label>
          <input defaultValue={week.phase} id="week-phase" name="phase" required />
        </div>
        <div className="field span-two">
          <label htmlFor="week-objective">Objective</label>
          <textarea defaultValue={week.objective} id="week-objective" name="objective" required rows={4} />
        </div>
        <div className="field span-two">
          <label htmlFor="week-deliverable">Deliverable</label>
          <textarea defaultValue={week.deliverable} id="week-deliverable" name="deliverable" required rows={3} />
        </div>
        <div className="field span-two">
          <label htmlFor="week-risks">Risks</label>
          <textarea defaultValue={week.risks.join("\n")} id="week-risks" name="risks" rows={4} />
          <small>Use one risk per line.</small>
        </div>
        <div className="field span-two">
          <label htmlFor="week-advisor">Advisor prompt</label>
          <textarea defaultValue={week.advisorPrompt} id="week-advisor" name="advisorPrompt" required rows={3} />
        </div>
        <div className="field span-two">
          <label htmlFor="week-reflection">Reflection</label>
          <textarea defaultValue={week.reflection} id="week-reflection" name="reflection" rows={5} />
        </div>
        <div className="field">
          <label htmlFor="week-planned">Planned minutes</label>
          <input defaultValue={week.plannedMinutes} id="week-planned" min="0" name="plannedMinutes" type="number" />
        </div>
        <div className="field">
          <label htmlFor="week-actual">Actual minutes</label>
          <input defaultValue={week.actualMinutes} id="week-actual" min="0" name="actualMinutes" type="number" />
        </div>
        <div className="field">
          <label htmlFor="week-state">Working state</label>
          <select defaultValue={week.state === "closed" ? "active" : week.state} id="week-state" name="state">
            <option value="planned">Planned</option>
            <option value="active">Active</option>
            <option value="blocked">Blocked</option>
          </select>
          {week.state === "closed" ? <small>Reopen the week before editing its working state.</small> : null}
        </div>
      </div>
      <div className="form-footer">
        <ActionFeedback state={state} />
        <SubmitButton>Save week</SubmitButton>
      </div>
    </form>
  );
}

export function TaskForm({ task, weekNumber }: { task: Task; weekNumber: number }) {
  const [state, action] = useActionState(updateTaskAction, initialActionState);
  const fieldPrefix = `task-${task.id}`;
  return (
    <form action={action} className="record-form">
      <input name="id" type="hidden" value={task.id} />
      <input name="weekNumber" type="hidden" value={weekNumber} />
      <input name="version" type="hidden" value={task.version} />
      <div className="record-form-heading">
        <div>
          <span>Task {task.position}</span>
          <h3>{task.title}</h3>
        </div>
        <label className="check-field" htmlFor={`${fieldPrefix}-required`}>
          <input
            defaultChecked={task.required}
            id={`${fieldPrefix}-required`}
            name="required"
            type="checkbox"
          />
          Required
        </label>
      </div>
      <div className="field-grid compact-fields">
        <div className="field span-two">
          <label htmlFor={`${fieldPrefix}-title`}>Title</label>
          <input defaultValue={task.title} id={`${fieldPrefix}-title`} name="title" required />
        </div>
        <div className="field">
          <label htmlFor={`${fieldPrefix}-position`}>Order</label>
          <input
            defaultValue={task.position}
            id={`${fieldPrefix}-position`}
            min="1"
            name="position"
            required
            type="number"
          />
          <small>Order values must be unique within the week.</small>
        </div>
        <div className="field">
          <label htmlFor={`${fieldPrefix}-estimate`}>Estimated minutes</label>
          <input
            defaultValue={task.estimateMinutes}
            id={`${fieldPrefix}-estimate`}
            min="0"
            name="estimateMinutes"
            required
            type="number"
          />
        </div>
        <div className="field span-two">
          <label htmlFor={`${fieldPrefix}-details`}>Details</label>
          <textarea defaultValue={task.details} id={`${fieldPrefix}-details`} name="details" rows={3} />
        </div>
        <div className="field span-two">
          <label htmlFor={`${fieldPrefix}-output`}>Expected evidence</label>
          <textarea
            defaultValue={task.expectedOutput}
            id={`${fieldPrefix}-output`}
            name="expectedOutput"
            required
            rows={3}
          />
        </div>
        <div className="field">
          <label htmlFor={`${fieldPrefix}-state`}>State</label>
          <select defaultValue={task.state} id={`${fieldPrefix}-state`} name="state">
            <option value="todo">To do</option>
            <option value="in_progress">In progress</option>
            <option value="blocked">Blocked</option>
            <option value="done">Done</option>
            <option value="skipped">Skipped</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor={`${fieldPrefix}-evidence`}>Evidence URL</label>
          <input
            defaultValue={task.evidenceUrl ?? ""}
            id={`${fieldPrefix}-evidence`}
            inputMode="url"
            name="evidenceUrl"
            type="url"
          />
        </div>
        <div className="field span-two">
          <label htmlFor={`${fieldPrefix}-note`}>Completion note or requirement-change reason</label>
          <textarea
            defaultValue={task.completionNote}
            id={`${fieldPrefix}-note`}
            name="completionNote"
            rows={3}
          />
        </div>
      </div>
      <div className="form-footer">
        <ActionFeedback state={state} />
        <SubmitButton>Save task</SubmitButton>
      </div>
    </form>
  );
}

export function GateForm({ gate, weekNumber }: { gate: Gate; weekNumber: number }) {
  const [state, action] = useActionState(updateGateAction, initialActionState);
  const fieldPrefix = `gate-${gate.id}`;
  return (
    <form action={action} className="record-form gate-form">
      <input name="id" type="hidden" value={gate.id} />
      <input name="weekNumber" type="hidden" value={weekNumber} />
      <input name="version" type="hidden" value={gate.version} />
      <div className="record-form-heading">
        <div>
          <span>Gate {gate.position}</span>
          <h3>{gate.criterion}</h3>
        </div>
        <label className="check-field" htmlFor={`${fieldPrefix}-required`}>
          <input
            defaultChecked={gate.required}
            id={`${fieldPrefix}-required`}
            name="required"
            type="checkbox"
          />
          Required
        </label>
      </div>
      <div className="field-grid compact-fields">
        <div className="field span-two">
          <label htmlFor={`${fieldPrefix}-criterion`}>Criterion</label>
          <textarea
            defaultValue={gate.criterion}
            id={`${fieldPrefix}-criterion`}
            name="criterion"
            required
            rows={3}
          />
        </div>
        <div className="field">
          <label htmlFor={`${fieldPrefix}-position`}>Order</label>
          <input
            defaultValue={gate.position}
            id={`${fieldPrefix}-position`}
            min="1"
            name="position"
            required
            type="number"
          />
          <small>Order values must be unique within the week.</small>
        </div>
        <div className="field">
          <label htmlFor={`${fieldPrefix}-state`}>Decision</label>
          <select defaultValue={gate.state} id={`${fieldPrefix}-state`} name="state">
            <option value="pending">Pending</option>
            <option value="met">Met</option>
            <option value="waived">Waived</option>
          </select>
        </div>
        <div className="field span-two">
          <label htmlFor={`${fieldPrefix}-evidence`}>Evidence</label>
          <textarea defaultValue={gate.evidence} id={`${fieldPrefix}-evidence`} name="evidence" rows={3} />
        </div>
        <div className="field span-two">
          <label htmlFor={`${fieldPrefix}-waiver`}>Waiver reason</label>
          <textarea
            defaultValue={gate.waiverReason}
            id={`${fieldPrefix}-waiver`}
            name="waiverReason"
            rows={3}
          />
        </div>
      </div>
      <div className="form-footer">
        <ActionFeedback state={state} />
        <SubmitButton>Save gate</SubmitButton>
      </div>
    </form>
  );
}

export function CreateTaskForm({ week }: { week: Week }) {
  const [state, action] = useActionState(createTaskAction, initialActionState);
  return (
    <details className="create-record">
      <summary>Add a task</summary>
      <form action={action} className="record-form">
        <input name="weekId" type="hidden" value={week.id} />
        <input name="weekNumber" type="hidden" value={week.number} />
        <div className="field-grid compact-fields">
          <div className="field">
            <label htmlFor="new-task-title">Title</label>
            <input id="new-task-title" name="title" required />
          </div>
          <div className="field">
            <label htmlFor="new-task-estimate">Estimated minutes</label>
            <input defaultValue="60" id="new-task-estimate" min="0" name="estimateMinutes" type="number" />
          </div>
          <div className="field span-two">
            <label htmlFor="new-task-details">Details</label>
            <textarea id="new-task-details" name="details" rows={3} />
          </div>
          <div className="field span-two">
            <label htmlFor="new-task-output">Expected evidence</label>
            <textarea id="new-task-output" name="expectedOutput" required rows={3} />
          </div>
          <label className="check-field" htmlFor="new-task-required">
            <input defaultChecked id="new-task-required" name="required" type="checkbox" />
            Required
          </label>
        </div>
        <div className="form-footer">
          <ActionFeedback state={state} />
          <SubmitButton pendingLabel="Adding">Add task</SubmitButton>
        </div>
      </form>
    </details>
  );
}

export function CreateGateForm({ week }: { week: Week }) {
  const [state, action] = useActionState(createGateAction, initialActionState);
  return (
    <details className="create-record">
      <summary>Add a gate</summary>
      <form action={action} className="record-form gate-form">
        <input name="weekId" type="hidden" value={week.id} />
        <input name="weekNumber" type="hidden" value={week.number} />
        <div className="field-grid compact-fields">
          <div className="field span-two">
            <label htmlFor="new-gate-criterion">Criterion</label>
            <textarea id="new-gate-criterion" name="criterion" required rows={3} />
          </div>
          <label className="check-field" htmlFor="new-gate-required">
            <input defaultChecked id="new-gate-required" name="required" type="checkbox" />
            Required
          </label>
        </div>
        <div className="form-footer">
          <ActionFeedback state={state} />
          <SubmitButton pendingLabel="Adding">Add gate</SubmitButton>
        </div>
      </form>
    </details>
  );
}

export function WeekClosureForm({ week }: { week: Week }) {
  const action = week.state === "closed" ? reopenWeekAction : closeWeekAction;
  const [state, formAction] = useActionState(action, initialActionState);
  return (
    <form action={formAction} className="closure-form">
      <input name="id" type="hidden" value={week.id} />
      <input name="number" type="hidden" value={week.number} />
      <input name="version" type="hidden" value={week.version} />
      {week.state === "closed" ? (
        <>
          <div className="field">
            <label htmlFor="reopen-reason">Reason for reopening</label>
            <textarea id="reopen-reason" name="reason" required rows={3} />
          </div>
        </>
      ) : (
        <p>Closing unlocks the next week. Every required task and gate must be resolved first.</p>
      )}
      <div className="form-footer">
        <ActionFeedback state={state} />
        <SubmitButton className={week.state === "closed" ? "button secondary compact-button" : "button primary compact-button"}>
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
      <div className="field">
        <label htmlFor="closed-reflection">Reflection</label>
        <textarea
          defaultValue={week.reflection}
          id="closed-reflection"
          name="reflection"
          rows={6}
        />
        <small>Reflection remains editable while the plan itself is closed.</small>
      </div>
      <div className="form-footer">
        <ActionFeedback state={state} />
        <SubmitButton>Save reflection</SubmitButton>
      </div>
    </form>
  );
}
