"use client";

import {
  BookOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  LeftOutlined,
  LinkOutlined,
  RightOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import { Alert, Breadcrumb, Button, Card, Collapse, Listy, Space, Tag, Typography } from "antd";
import Link from "next/link";
import { CurrentWeekMarker } from "@/components/current-week";
import { DataNotice } from "@/components/data-notice";
import { InternalLinkButton } from "@/components/internal-link-button";
import { MarkdownText } from "@/components/markdown-text";
import { PriorityBrief } from "@/components/priority-brief";
import { StatusLabel } from "@/components/status-label";
import { formatDateRange, weekCanClose, weekIsReady, weekProgress } from "@/lib/domain";
import type { LoadedPlan, Week } from "@/lib/schema";

type WeekDetailPlan = Pick<
  LoadedPlan,
  "dataSource" | "lastRefreshedAt" | "sources" | "weekSources"
> & {
  project: Pick<LoadedPlan["project"], "timezone">;
  weeks: Week[];
};

function formatHours(minutes: number): string {
  const hours = minutes / 60;
  return (Number.isInteger(hours) ? hours : hours.toFixed(1)) + "h";
}

export function WeekDetailView({
  plan,
  weekNumber,
}: {
  plan: WeekDetailPlan;
  weekNumber: number;
}) {
  const week = plan.weeks.find((candidate) => candidate.number === weekNumber);
  if (!week) return null;

  const progress = weekProgress(week);
  const ready = weekIsReady(plan.weeks, week.number);
  const previous = plan.weeks.find((candidate) => candidate.number === week.number - 1);
  const next = plan.weeks.find((candidate) => candidate.number === week.number + 1);
  const previousRequiredGates = previous?.gates.filter((gate) => gate.required) ?? [];
  const previousResolvedGates = previousRequiredGates.filter(
    (gate) => gate.state === "met" || gate.state === "waived",
  ).length;
  const nextRequiredTask = week.tasks.find((task) => task.required && task.state !== "done");
  const nextRequiredGate = week.gates.find((gate) => gate.required && gate.state === "pending");
  const sourceLinks = plan.weekSources
    .filter((link) => link.weekId === week.id)
    .flatMap((link) => {
      const source = plan.sources.find((candidate) => candidate.id === link.sourceId);
      return source ? [{ ...link, source }] : [];
    });

  const nextStepTitle = nextRequiredTask
    ? nextRequiredTask.title
    : nextRequiredGate
      ? "Resolve the remaining advancement decision"
      : weekCanClose(week)
        ? "Review the completed week"
        : "Review the weekly record";
  const nextStepDescription = nextRequiredTask
    ? "Evidence to produce: " + nextRequiredTask.expectedOutput
    : nextRequiredGate
      ? "All required tasks are complete. Record whether the remaining condition was met or waived."
      : "All required work is resolved. Review the record before the plan moves forward.";
  const nextStepHref = nextRequiredTask
    ? "#weekly-work"
    : nextRequiredGate
      ? "#decisions"
      : "#finish-line";
  const nextStepLabel = nextRequiredTask
    ? "Review next task"
    : nextRequiredGate
      ? "Review decision"
      : "Review finish line";

  return (
    <div className="shell page-shell">
      <DataNotice dataSource={plan.dataSource} lastRefreshedAt={plan.lastRefreshedAt} />
      <Breadcrumb
        className="breadcrumbs"
        items={[
          { title: <Link href="/">Overview</Link> },
          { title: "Week " + week.number },
        ]}
      />

      <header className="week-header">
        <div>
          <p className="eyebrow">Week {week.number} · {week.phase}</p>
          <h1>{week.title}</h1>
          <p className="page-summary">
            The aim is simple: complete this week&apos;s work, record what proves it is finished,
            and make the decisions required before moving on.
          </p>
          <Typography.Paragraph className="week-objective" type="secondary">
            <Typography.Text strong>Research objective: </Typography.Text>
            {week.objective}
          </Typography.Paragraph>
          <div className="week-kicker">
            <span>{formatDateRange(week.startDate, week.endDate)}</span>
            <span>{formatHours(week.plannedMinutes)} planned</span>
            <span>{formatHours(week.actualMinutes)} actual</span>
          </div>
        </div>
        <Space className="week-status-stack" size={[8, 8]} wrap>
          <StatusLabel status={week.state} />
          <Tag
            bordered
            icon={ready ? <CheckCircleOutlined /> : <WarningOutlined />}
          >
            {ready ? "Prerequisites ready" : "Prerequisites blocked"}
          </Tag>
          <CurrentWeekMarker
            startDate={week.startDate}
            endDate={week.endDate}
            timezone={plan.project.timezone}
          />
        </Space>
      </header>

      <PriorityBrief
        actionHref={nextStepHref}
        actionLabel={nextStepLabel}
        decision={
          nextRequiredGate ? (
            <p>{nextRequiredGate.criterion}</p>
          ) : (
            <p className="muted">Every required advancement decision is recorded.</p>
          )
        }
        deliverable={<p id="finish-line">{week.deliverable}</p>}
        nextDescription={nextStepDescription}
        nextTitle={nextStepTitle}
        progress={{
          percent: progress.percent,
          label: progress.completed + " of " + progress.required + " required tasks complete",
        }}
      />

      {!previous ? (
        <Alert
          className="dependency-alert"
          description={
            <Space direction="vertical" size={16}>
              <Typography.Text>
                There is no earlier weekly gate. Confirm the manual access actions and protocol
                approvals as part of Week 1.
              </Typography.Text>
              <InternalLinkButton href="/protocol#manual-actions">
                Review manual actions
              </InternalLinkButton>
            </Space>
          }
          icon={<ClockCircleOutlined />}
          title={<h2 id="prerequisites-title">Begin from the locked protocol.</h2>}
          showIcon
          type="info"
        />
      ) : !ready ? (
        <Alert
          className="dependency-alert"
          description={
            <Space direction="vertical" size={16}>
              <Typography.Text>
                {previousResolvedGates} of {previousRequiredGates.length} required advancement gates
                are decided. This week becomes ready only when the previous week is closed.
              </Typography.Text>
              <InternalLinkButton
                block
                href={"/weeks/" + previous.number}
                style={{ height: "auto", whiteSpace: "normal" }}
              >
                Week {previous.number}: {previous.title}
              </InternalLinkButton>
            </Space>
          }
          icon={<WarningOutlined />}
          title={<h2 id="prerequisites-title">Close Week {previous.number} before starting.</h2>}
          showIcon
          type="warning"
        />
      ) : null}

      <div className="week-content-grid">
        <section aria-labelledby="tasks-title" className="week-main-column" id="weekly-work">
          <div className="section-heading compact">
            <div>
              <p className="eyebrow">Execution</p>
              <h2 id="tasks-title">Work for the week</h2>
            </div>
            <p>Open a task for its instructions and the evidence needed to count it as complete.</p>
          </div>
          {week.tasks.length > 0 ? (
            <Collapse
              className="task-collapse"
              defaultActiveKey={nextRequiredTask ? [nextRequiredTask.id] : []}
              items={week.tasks.map((task) => ({
                key: task.id,
                forceRender: true,
                label: (
                  <div className="task-heading">
                    <span className="task-position">{task.position}</span>
                    <div>
                      <h3>{task.title}</h3>
                      <div className="task-meta">
                        <StatusLabel status={task.state} />
                        <span>{formatHours(task.estimateMinutes)} estimate</span>
                        <Tag bordered>{task.required ? "Required" : "Optional"}</Tag>
                      </div>
                    </div>
                  </div>
                ),
                children: (
                  <article className="task-detail" id={"task-" + task.id}>
                    <MarkdownText>{task.details}</MarkdownText>
                    <div className="evidence-box">
                      <Typography.Text strong>Expected evidence</Typography.Text>
                      <p>{task.expectedOutput}</p>
                      {task.completionNote ? (
                        <p className="completion-note">{task.completionNote}</p>
                      ) : null}
                      {task.evidenceUrl ? (
                        <Button
                          href={task.evidenceUrl}
                          icon={<LinkOutlined />}
                          rel="noreferrer"
                          target="_blank"
                          type="link"
                        >
                          Open evidence
                        </Button>
                      ) : null}
                    </div>
                  </article>
                ),
              }))}
            />
          ) : (
            <Card>
              <Typography.Text type="secondary">No tasks are recorded for this week.</Typography.Text>
            </Card>
          )}
        </section>

        <aside className="week-side-column">
          {sourceLinks.length > 0 ? (
            <section aria-labelledby="reading-title">
              <Card
                className="week-side-card"
                title={<h2 id="reading-title">Read before working</h2>}
              >
                <div className="reading-list" role="list">
                  <Listy
                    itemRender={({ source, purpose, priority }) => (
                      <div role="listitem">
                      <div className="reading-list-item">
                        <Space align="start" size={8}>
                          <BookOutlined />
                          <a href={source.canonicalUrl} rel="noreferrer" target="_blank">
                            {source.title} <LinkOutlined aria-hidden="true" />
                          </a>
                        </Space>
                        <Typography.Paragraph type="secondary">{purpose}</Typography.Paragraph>
                        <Tag bordered>{priority === "required" ? "Required" : "Recommended"}</Tag>
                      </div>
                      </div>
                    )}
                    items={sourceLinks}
                    rowKey={({ source }) => source.id}
                  />
                </div>
              </Card>
            </section>
          ) : null}

          <section aria-labelledby="gates-title" id="decisions">
            <Card
              className="week-side-card"
              extra={
                <Tag bordered>
                  {week.gates.filter((gate) => gate.state === "pending").length} pending
                </Tag>
              }
              title={<h2 id="gates-title">Advance when</h2>}
            >
              {week.gates.length > 0 ? (
                <div className="decision-list" role="list">
                  <Listy
                    itemRender={(gate) => (
                      <div role="listitem">
                      <div className="decision-list-item">
                        <Space size={[6, 6]} wrap>
                          <StatusLabel status={gate.state} />
                          <Tag bordered>{gate.required ? "Required" : "Optional"}</Tag>
                        </Space>
                        <p>{gate.criterion}</p>
                        {gate.evidence ? (
                          <Typography.Text type="secondary">
                            Evidence: {gate.evidence}
                          </Typography.Text>
                        ) : null}
                        {gate.waiverReason ? (
                          <Typography.Text type="secondary">
                            Waiver: {gate.waiverReason}
                          </Typography.Text>
                        ) : null}
                      </div>
                      </div>
                    )}
                    items={week.gates}
                    rowKey="id"
                  />
                </div>
              ) : (
                <Typography.Text type="secondary">
                  No advancement decisions are recorded.
                </Typography.Text>
              )}
              <Alert
                icon={weekCanClose(week) ? <CheckCircleOutlined /> : <ClockCircleOutlined />}
                title={
                  weekCanClose(week)
                    ? "Every required condition is satisfied."
                    : "Required conditions remain open."
                }
                showIcon
                type={weekCanClose(week) ? "success" : "info"}
              />
            </Card>
          </section>

          <section aria-labelledby="advisor-title">
            <Card
              className="week-side-card"
              title={<h2 id="advisor-title">Advisor checkpoint</h2>}
            >
              <p>{week.advisorPrompt}</p>
            </Card>
          </section>

          {week.risks.length > 0 ? (
            <section aria-labelledby="risks-title">
              <Collapse
                className="side-collapse"
                items={[
                  {
                    key: "risks",
                    forceRender: true,
                    label: <h2 id="risks-title">Watch closely</h2>,
                    children: (
                      <div className="risk-list" role="list">
                        <Listy
                          itemRender={(risk) => <div role="listitem">{risk}</div>}
                          items={week.risks}
                          rowKey={(risk) => risk}
                        />
                      </div>
                    ),
                  },
                ]}
              />
            </section>
          ) : null}

          {week.reflection ? (
            <section aria-labelledby="reflection-title">
              <Collapse
                className="side-collapse"
                items={[
                  {
                    key: "reflection",
                    forceRender: true,
                    label: <h2 id="reflection-title">Reflection</h2>,
                    children: <MarkdownText>{week.reflection}</MarkdownText>,
                  },
                ]}
              />
            </section>
          ) : null}
        </aside>
      </div>

      <nav className="week-pagination" aria-label="Week navigation">
        {previous ? (
          <InternalLinkButton href={"/weeks/" + previous.number} icon={<LeftOutlined />}>
            Previous: {previous.title}
          </InternalLinkButton>
        ) : (
          <span />
        )}
        {next ? (
          <InternalLinkButton
            href={"/weeks/" + next.number}
            icon={<RightOutlined />}
            iconPlacement="end"
          >
            Next: {next.title}
          </InternalLinkButton>
        ) : (
          <InternalLinkButton href="/" icon={<RightOutlined />} iconPlacement="end">
            Return to overview
          </InternalLinkButton>
        )}
      </nav>
    </div>
  );
}
