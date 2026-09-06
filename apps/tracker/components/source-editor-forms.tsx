"use client";

import { useActionState } from "react";
import {
  createSourceAction,
  linkSourceAction,
  updateSourceAction,
} from "@/app/actions";
import { ActionFeedback } from "@/components/action-feedback";
import { SubmitButton } from "@/components/submit-button";
import { initialActionState } from "@/lib/action-state";
import type { Source, Week } from "@/lib/schema";

type SourceChoice = Pick<Source, "id" | "title">;
type WeekChoice = Pick<Week, "id" | "number" | "state" | "title">;

export function SourceForm({ source }: { source: Source }) {
  const [state, action] = useActionState(updateSourceAction, initialActionState);
  const prefix = `source-${source.id}`;
  return (
    <form action={action} className="record-form source-editor-form">
      <input name="id" type="hidden" value={source.id} />
      <input name="version" type="hidden" value={source.version} />
      <div className="record-form-heading">
        <div>
          <span>Source record {source.version}</span>
          <h3>{source.title}</h3>
        </div>
        <a href={source.canonicalUrl} rel="noreferrer" target="_blank">Open source</a>
      </div>
      <div className="field-grid compact-fields">
        <div className="field span-two">
          <label htmlFor={`${prefix}-title`}>Title</label>
          <input defaultValue={source.title} id={`${prefix}-title`} name="title" required />
        </div>
        <div className="field">
          <label htmlFor={`${prefix}-authors`}>Authors</label>
          <input defaultValue={source.authors} id={`${prefix}-authors`} name="authors" required />
        </div>
        <div className="field">
          <label htmlFor={`${prefix}-year`}>Year</label>
          <input defaultValue={source.year} id={`${prefix}-year`} min="1900" name="year" required type="number" />
        </div>
        <div className="field span-two">
          <label htmlFor={`${prefix}-url`}>Canonical HTTPS URL</label>
          <input
            defaultValue={source.canonicalUrl}
            id={`${prefix}-url`}
            name="canonicalUrl"
            required
            type="url"
          />
        </div>
        <div className="field span-two">
          <label htmlFor={`${prefix}-purpose`}>Project purpose</label>
          <textarea defaultValue={source.purpose} id={`${prefix}-purpose`} name="purpose" required rows={3} />
        </div>
        <div className="field">
          <label htmlFor={`${prefix}-verified`}>Verified on</label>
          <input
            defaultValue={source.verifiedAt}
            id={`${prefix}-verified`}
            name="verifiedAt"
            required
            type="date"
          />
        </div>
      </div>
      <div className="form-footer">
        <ActionFeedback state={state} />
        <SubmitButton>Save source</SubmitButton>
      </div>
    </form>
  );
}

export function CreateSourceForm() {
  const [state, action] = useActionState(createSourceAction, initialActionState);
  return (
    <details className="create-record">
      <summary>Add a source</summary>
      <form action={action} className="record-form source-editor-form">
        <div className="field-grid compact-fields">
          <div className="field span-two">
            <label htmlFor="new-source-title">Title</label>
            <input id="new-source-title" name="title" required />
          </div>
          <div className="field">
            <label htmlFor="new-source-authors">Authors</label>
            <input id="new-source-authors" name="authors" required />
          </div>
          <div className="field">
            <label htmlFor="new-source-year">Year</label>
            <input id="new-source-year" min="1900" name="year" required type="number" />
          </div>
          <div className="field span-two">
            <label htmlFor="new-source-url">Canonical HTTPS URL</label>
            <input id="new-source-url" name="canonicalUrl" required type="url" />
          </div>
          <div className="field span-two">
            <label htmlFor="new-source-purpose">Project purpose</label>
            <textarea id="new-source-purpose" name="purpose" required rows={3} />
          </div>
          <div className="field">
            <label htmlFor="new-source-verified">Verified on</label>
            <input id="new-source-verified" name="verifiedAt" required type="date" />
          </div>
        </div>
        <div className="form-footer">
          <ActionFeedback state={state} />
          <SubmitButton pendingLabel="Adding">Add source</SubmitButton>
        </div>
      </form>
    </details>
  );
}

export function LinkSourceForm({ sources, weeks }: { sources: SourceChoice[]; weeks: WeekChoice[] }) {
  const [state, action] = useActionState(linkSourceAction, initialActionState);
  const openWeeks = weeks.filter((week) => week.state !== "closed");
  const canLink = sources.length > 0 && openWeeks.length > 0;
  return (
    <form action={action} className="record-form source-link-form">
      <div className="record-form-heading">
        <div>
          <span>Week reading</span>
          <h3>Link a source to an open week</h3>
        </div>
      </div>
      <div className="field-grid compact-fields">
        <div className="field">
          <label htmlFor="link-source">Source</label>
          <select disabled={!canLink} id="link-source" name="sourceId" required>
            <option value="">Choose a source</option>
            {sources.map((source) => <option key={source.id} value={source.id}>{source.title}</option>)}
          </select>
        </div>
        <div className="field">
          <label htmlFor="link-week">Week</label>
          <select disabled={!canLink} id="link-week" name="weekId" required>
            <option value="">Choose an open week</option>
            {openWeeks.map((week) => <option key={week.id} value={week.id}>Week {week.number}: {week.title}</option>)}
          </select>
          <small>Closed weeks must be reopened before their reading list can change.</small>
        </div>
        <div className="field span-two">
          <label htmlFor="link-purpose">Purpose for this week</label>
          <textarea disabled={!canLink} id="link-purpose" name="purpose" required rows={3} />
        </div>
        <div className="field">
          <label htmlFor="link-priority">Priority</label>
          <select defaultValue="recommended" disabled={!canLink} id="link-priority" name="priority">
            <option value="required">Required</option>
            <option value="recommended">Recommended</option>
          </select>
        </div>
      </div>
      <div className="form-footer">
        <ActionFeedback state={state} />
        <SubmitButton disabled={!canLink} pendingLabel="Linking">Link source</SubmitButton>
      </div>
    </form>
  );
}
