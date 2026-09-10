"use client";

import { BookOutlined, ExportOutlined, LinkOutlined, PlusOutlined } from "@ant-design/icons";
import { Alert, Button, Collapse, Empty, Form, Input, Select } from "antd";
import { useActionState, useState } from "react";
import { createSourceAction, linkSourceAction, updateSourceAction } from "@/app/actions";
import { ActionFeedback } from "@/components/action-feedback";
import { SubmitButton } from "@/components/submit-button";
import { initialActionState } from "@/lib/action-state";
import type { Source, Week } from "@/lib/schema";

const FormItem = Form.Item;
const TextArea = Input.TextArea;

type SourceChoice = Pick<Source, "id" | "title">;
type WeekChoice = Pick<Week, "id" | "number" | "state" | "title">;

export function SourceManagement({
  sources,
  weekSourcesCount,
  weeks,
}: {
  sources: Source[];
  weekSourcesCount: number;
  weeks: WeekChoice[];
}) {
  return (
    <Collapse
      className="source-management-collapse"
      items={[
        {
          children: (
            <>
              <div className="editor-record-list">
                {sources.length > 0 ? (
                  sources.map((source) => <SourceForm key={source.id} source={source} />)
                ) : (
                  <Empty description="No sources yet" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                )}
              </div>
              <CreateSourceForm />
            </>
          ),
          key: "source-library",
          label: (
            <span className="collapse-section-label">
              <BookOutlined />
              <span>
                <strong>Source library</strong>
                <small>{sources.length} public-safe sources</small>
              </span>
            </span>
          ),
        },
        {
          children: <LinkSourceForm sources={sources} weeks={weeks} />,
          key: "weekly-reading",
          label: (
            <span className="collapse-section-label">
              <LinkOutlined />
              <span>
                <strong>Weekly reading links</strong>
                <small>{weekSourcesCount} links between sources and weekly work</small>
              </span>
            </span>
          ),
        },
      ]}
    />
  );
}

export function SourceForm({ source }: { source: Source }) {
  const [state, action] = useActionState(updateSourceAction, initialActionState);
  const prefix = `source-${source.id}`;
  return (
    <Collapse
      className="record-collapse source-record-collapse"
      items={[
        {
          children: (
            <form action={action} className="record-form source-editor-form">
              <input name="id" type="hidden" value={source.id} />
              <input name="version" type="hidden" value={source.version} />
              <div className="record-form-heading">
                <span>Source record {source.version}</span>
                <Button
                  href={source.canonicalUrl}
                  icon={<ExportOutlined />}
                  rel="noreferrer"
                  target="_blank"
                >
                  Open source
                </Button>
              </div>
              <Form component={false} layout="vertical">
                <div className="field-grid compact-fields">
                  <FormItem className="field span-two" htmlFor={`${prefix}-title`} label="Title" required>
                    <Input defaultValue={source.title} id={`${prefix}-title`} name="title" required />
                  </FormItem>
                  <FormItem className="field" htmlFor={`${prefix}-authors`} label="Authors" required>
                    <Input defaultValue={source.authors} id={`${prefix}-authors`} name="authors" required />
                  </FormItem>
                  <FormItem className="field" htmlFor={`${prefix}-year`} label="Year" required>
                    <Input defaultValue={source.year} id={`${prefix}-year`} min="1900" name="year" required type="number" />
                  </FormItem>
                  <FormItem className="field span-two" htmlFor={`${prefix}-url`} label="Canonical HTTPS URL" required>
                    <Input defaultValue={source.canonicalUrl} id={`${prefix}-url`} name="canonicalUrl" required type="url" />
                  </FormItem>
                  <FormItem className="field span-two" htmlFor={`${prefix}-purpose`} label="Project purpose" required>
                    <TextArea defaultValue={source.purpose} id={`${prefix}-purpose`} name="purpose" required rows={3} />
                  </FormItem>
                  <FormItem className="field" htmlFor={`${prefix}-verified`} label="Verified on" required>
                    <Input defaultValue={source.verifiedAt} id={`${prefix}-verified`} name="verifiedAt" required type="date" />
                  </FormItem>
                </div>
              </Form>
              <div className="form-footer">
                <ActionFeedback state={state} />
                <SubmitButton>Save source</SubmitButton>
              </div>
            </form>
          ),
          key: source.id,
          label: (
            <span className="record-collapse-label">
              <small>{source.year}</small>
              <strong>{source.title}</strong>
            </span>
          ),
        },
      ]}
    />
  );
}

export function CreateSourceForm() {
  const [state, action] = useActionState(createSourceAction, initialActionState);
  return (
    <Collapse
      className="create-record"
      items={[
        {
          children: (
            <form action={action} className="record-form source-editor-form">
              <Form component={false} layout="vertical">
                <div className="field-grid compact-fields">
                  <FormItem className="field span-two" htmlFor="new-source-title" label="Title" required>
                    <Input id="new-source-title" name="title" required />
                  </FormItem>
                  <FormItem className="field" htmlFor="new-source-authors" label="Authors" required>
                    <Input id="new-source-authors" name="authors" required />
                  </FormItem>
                  <FormItem className="field" htmlFor="new-source-year" label="Year" required>
                    <Input id="new-source-year" min="1900" name="year" required type="number" />
                  </FormItem>
                  <FormItem className="field span-two" htmlFor="new-source-url" label="Canonical HTTPS URL" required>
                    <Input id="new-source-url" name="canonicalUrl" required type="url" />
                  </FormItem>
                  <FormItem className="field span-two" htmlFor="new-source-purpose" label="Project purpose" required>
                    <TextArea id="new-source-purpose" name="purpose" required rows={3} />
                  </FormItem>
                  <FormItem className="field" htmlFor="new-source-verified" label="Verified on" required>
                    <Input id="new-source-verified" name="verifiedAt" required type="date" />
                  </FormItem>
                </div>
              </Form>
              <div className="form-footer">
                <ActionFeedback state={state} />
                <SubmitButton pendingLabel="Adding">Add source</SubmitButton>
              </div>
            </form>
          ),
          key: "create-source",
          label: <span className="create-record-label"><PlusOutlined /> Add a source</span>,
        },
      ]}
    />
  );
}

export function LinkSourceForm({ sources, weeks }: { sources: SourceChoice[]; weeks: WeekChoice[] }) {
  const [state, action] = useActionState(linkSourceAction, initialActionState);
  const [sourceId, setSourceId] = useState("");
  const [weekId, setWeekId] = useState("");
  const [priority, setPriority] = useState("recommended");
  const openWeeks = weeks.filter((week) => week.state !== "closed");
  const canLink = sources.length > 0 && openWeeks.length > 0;
  const canSubmit = canLink && sourceId.length > 0 && weekId.length > 0;

  return (
    <form action={action} className="record-form source-link-form">
      {!canLink ? (
        <Alert
          description="Add a source and make sure at least one week is open before creating a reading link."
          title="A reading link cannot be created yet."
          showIcon
          type="info"
        />
      ) : null}
      <input name="sourceId" type="hidden" value={sourceId} />
      <input name="weekId" type="hidden" value={weekId} />
      <input name="priority" type="hidden" value={priority} />
      <Form component={false} layout="vertical">
        <div className="field-grid compact-fields">
          <FormItem className="field" htmlFor="link-source" label="Source" required>
            <Select
              disabled={!canLink}
              id="link-source"
              onChange={setSourceId}
              options={sources.map((source) => ({ label: source.title, value: source.id }))}
              placeholder="Choose a source"
              value={sourceId || undefined}
            />
          </FormItem>
          <FormItem
            className="field"
            extra="Closed weeks must be reopened before their reading list can change."
            htmlFor="link-week"
            label="Week"
            required
          >
            <Select
              disabled={!canLink}
              id="link-week"
              onChange={setWeekId}
              options={openWeeks.map((week) => ({
                label: `Week ${week.number}: ${week.title}`,
                value: week.id,
              }))}
              placeholder="Choose an open week"
              value={weekId || undefined}
            />
          </FormItem>
          <FormItem className="field span-two" htmlFor="link-purpose" label="Purpose for this week" required>
            <TextArea disabled={!canLink} id="link-purpose" name="purpose" required rows={3} />
          </FormItem>
          <FormItem className="field" htmlFor="link-priority" label="Priority">
            <Select
              disabled={!canLink}
              id="link-priority"
              onChange={setPriority}
              options={[
                { label: "Required", value: "required" },
                { label: "Recommended", value: "recommended" },
              ]}
              value={priority}
            />
          </FormItem>
        </div>
      </Form>
      <div className="form-footer">
        <ActionFeedback state={state} />
        <SubmitButton disabled={!canSubmit} pendingLabel="Linking">Link source</SubmitButton>
      </div>
    </form>
  );
}
