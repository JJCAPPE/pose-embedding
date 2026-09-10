"use client";

import { ArrowRightOutlined, CheckSquareOutlined, FileDoneOutlined } from "@ant-design/icons";
import { Card, Progress } from "antd";
import type { ReactNode } from "react";
import { InternalLinkButton } from "@/components/internal-link-button";

export function PriorityBrief({
  nextTitle,
  nextDescription,
  actionHref,
  actionLabel,
  deliverable,
  decision,
  progress,
}: {
  nextTitle: string;
  nextDescription?: string;
  actionHref?: string;
  actionLabel?: string;
  deliverable: ReactNode;
  decision: ReactNode;
  progress?: { percent: number; label: string };
}) {
  return (
    <section className="priority-brief" aria-label="What happens next">
      <div className="priority-top-row">
        <Card className="priority-card priority-card-primary">
          <p className="card-label"><CheckSquareOutlined /> Next step</p>
          <h2>{nextTitle}</h2>
          {nextDescription ? <p className="priority-description">{nextDescription}</p> : null}
          {progress ? (
            <div className="priority-progress">
              <Progress aria-label={progress.label} percent={progress.percent} showInfo={false} />
              <span>{progress.label}</span>
            </div>
          ) : null}
          {actionHref && actionLabel ? (
            <InternalLinkButton
              href={actionHref}
              icon={<ArrowRightOutlined />}
              iconPlacement="end"
              type="primary"
            >
              {actionLabel}
            </InternalLinkButton>
          ) : null}
        </Card>
        <Card className="priority-card priority-card-decision">
          <p className="card-label"><CheckSquareOutlined /> Decision needed</p>
          <div className="priority-decision-content">{decision}</div>
        </Card>
      </div>
      <Card className="priority-card priority-card-deliverable">
        <p className="card-label"><FileDoneOutlined /> Deliverable</p>
        <div className="priority-deliverable-content">{deliverable}</div>
      </Card>
    </section>
  );
}
