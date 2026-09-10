"use client";

import {
  ArrowRightOutlined,
  BookOutlined,
  CalendarOutlined,
  LinkOutlined,
  SafetyCertificateOutlined,
} from "@ant-design/icons";
import { Card, Empty, Listy, Space, Tag, Typography } from "antd";
import Link from "next/link";
import { DataNotice } from "@/components/data-notice";
import { InternalLinkButton } from "@/components/internal-link-button";
import { formatDateRange } from "@/lib/domain";
import type { LoadedPlan, Week } from "@/lib/schema";

type LiteraturePlan = Pick<
  LoadedPlan,
  "dataSource" | "lastRefreshedAt" | "sources" | "weekSources"
> & {
  weeks: Pick<Week, "id" | "number" | "state" | "title">[];
};

export function LiteratureView({ plan }: { plan: LiteraturePlan }) {
  const nextWeek =
    plan.weeks.find((week) => week.state !== "closed") ?? plan.weeks.at(-1);
  const weeksById = new Map(plan.weeks.map((week) => [week.id, week]));
  const sourcesById = new Map(plan.sources.map((source) => [source.id, source]));
  const usageBySource = new Map(
    plan.sources.map((source) => [
      source.id,
      plan.weekSources.flatMap((link) => {
        if (link.sourceId !== source.id) return [];
        const week = weeksById.get(link.weekId);
        return week ? [{ ...link, week }] : [];
      }),
    ]),
  );
  const requiredReading = nextWeek
    ? plan.weekSources.flatMap((link) => {
        if (link.weekId !== nextWeek.id || link.priority !== "required") return [];
        const source = sourcesById.get(link.sourceId);
        return source ? [{ ...link, source }] : [];
      })
    : [];

  return (
    <div className="shell page-shell">
      <DataNotice dataSource={plan.dataSource} lastRefreshedAt={plan.lastRefreshedAt} />
      <header className="page-header literature-header">
        <div>
          <p className="eyebrow">Evidence ledger</p>
          <h1>Sources behind the study.</h1>
          <p className="page-summary">
            These sources explain why each major study choice was made and where it is used.
          </p>
          <Typography.Paragraph className="literature-context" type="secondary">
            Every source is tied to a protocol choice, implementation check, or reporting
            constraint.
          </Typography.Paragraph>
        </div>
      </header>

      {nextWeek ? (
        <section aria-labelledby="next-reading-title" className="next-reading-section">
          <Card
            className="next-reading-card"
            title={
              <div>
                <p className="card-label"><BookOutlined /> Read next</p>
                <h2 id="next-reading-title">Required for Week {nextWeek.number}: {nextWeek.title}</h2>
              </div>
            }
          >
            {requiredReading.length > 0 ? (
              <div role="list">
                <Listy
                  className="next-reading-list"
                  itemRender={({ purpose, source }) => (
                    <div role="listitem">
                    <div className="next-reading-item">
                      <Typography.Title level={3}>
                        <a href={source.canonicalUrl} rel="noreferrer" target="_blank">
                          {source.title} <LinkOutlined aria-hidden="true" />
                        </a>
                      </Typography.Title>
                      <Typography.Paragraph type="secondary">{purpose}</Typography.Paragraph>
                      <Tag bordered>Required</Tag>
                    </div>
                    </div>
                  )}
                  items={requiredReading}
                  rowKey={({ source }) => source.id}
                />
              </div>
            ) : (
              <Empty
                description="This week has no required reading."
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            )}
            <InternalLinkButton
              block
              href={"/weeks/" + nextWeek.number}
              icon={<ArrowRightOutlined />}
              iconPlacement="end"
              style={{ marginTop: 24 }}
            >
              Open Week {nextWeek.number}
            </InternalLinkButton>
          </Card>
        </section>
      ) : null}

      <section aria-labelledby="sources-title" className="all-sources-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Full reference set</p>
            <h2 id="sources-title">All verified sources</h2>
          </div>
          <Tag bordered>{plan.sources.length} sources</Tag>
        </div>

        {plan.sources.length > 0 ? (
          <div className="source-ledger" role="list">
            <Listy
              itemRender={(source) => {
              const usages = usageBySource.get(source.id) ?? [];
              return (
                <div role="listitem">
                  <article className="source-list-item">
                    <div className="source-title-row">
                      <div>
                        <Space className="source-meta" size={[10, 8]} wrap>
                          <span>{source.authors}</span>
                          <span>{source.year}</span>
                        </Space>
                        <Typography.Title level={3}>
                          <a href={source.canonicalUrl} rel="noreferrer" target="_blank">
                            {source.title} <LinkOutlined aria-hidden="true" />
                          </a>
                        </Typography.Title>
                      </div>
                      <Space className="verification-meta" size={7}>
                        <SafetyCertificateOutlined />
                        <Typography.Text type="secondary">
                          Verified {formatDateRange(source.verifiedAt, source.verifiedAt)}
                        </Typography.Text>
                      </Space>
                    </div>

                    <div className="source-purpose">
                      <Typography.Text strong>Why it matters</Typography.Text>
                      <Typography.Paragraph>{source.purpose}</Typography.Paragraph>
                    </div>

                    <div className="source-usage">
                      <Space align="center" size={7}>
                        <CalendarOutlined />
                        <Typography.Text strong>Used in</Typography.Text>
                      </Space>
                      <Space className="source-week-tags" size={[6, 6]} wrap>
                        {usages.length > 0 ? (
                          usages.map(({ week }) => (
                            <Tag bordered key={week.id}>
                              <Link href={"/weeks/" + week.number}>Week {week.number}</Link>
                            </Tag>
                          ))
                        ) : (
                          <Tag bordered>Project-wide reference</Tag>
                        )}
                      </Space>
                    </div>
                  </article>
                </div>
              );
              }}
              items={plan.sources}
              rowKey="id"
            />
          </div>
        ) : (
          <Empty description="No verified sources are recorded." />
        )}
      </section>
    </div>
  );
}
