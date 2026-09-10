"use client";

import {
  ArrowRightOutlined,
  FileProtectOutlined,
  LockOutlined,
  QuestionCircleOutlined,
} from "@ant-design/icons";
import {
  Alert,
  Card,
  Collapse,
  Descriptions,
  Empty,
  Listy,
  Space,
  Tag,
  Timeline,
  Typography,
} from "antd";
import { DataNotice } from "@/components/data-notice";
import { InternalLinkButton } from "@/components/internal-link-button";
import { formatDateRange } from "@/lib/domain";
import type { LoadedPlan } from "@/lib/schema";

type ProtocolViewProps = Pick<
  LoadedPlan,
  "dataSource" | "lastRefreshedAt" | "manualActions" | "protocol"
> & {
  weekNumberByTaskId: Record<string, number>;
};

export function ProtocolView({
  dataSource,
  lastRefreshedAt,
  manualActions,
  protocol,
  weekNumberByTaskId,
}: ProtocolViewProps) {

  return (
    <div className="shell page-shell">
      <DataNotice dataSource={dataSource} lastRefreshedAt={lastRefreshedAt} />
      <header className="page-header protocol-header">
        <div>
          <p className="eyebrow">Locked study design</p>
          <h1>The rules before the result.</h1>
          <p className="page-summary">
            These rules keep the comparison fair by fixing the study before final results are
            opened. A neutral or negative result still counts as success.
          </p>
        </div>
      </header>

      <Alert
        className="protocol-success"
        description={protocol.successDefinition}
        icon={<FileProtectOutlined />}
        title="What counts as success"
        showIcon
        type="info"
      />

      <section className="protocol-section" aria-labelledby="manual-title" id="manual-actions">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Researcher actions</p>
            <h2 id="manual-title">Actions only you can complete</h2>
          </div>
          <p>
            These require your access, consent, or approval. Dates show when they are due, not
            whether they are complete.
          </p>
        </div>
        {manualActions.length > 0 ? (
          <Timeline
            className="manual-action-timeline"
            items={manualActions.map((action) => {
              const linkedWeekNumber = action.weekTaskId
                ? weekNumberByTaskId[action.weekTaskId]
                : undefined;
              return {
                key: action.id,
                content: (
                  <Card className="manual-action-card" size="small">
                    <Space size={[8, 8]} wrap>
                      <time dateTime={action.dueDate}>
                        Due {formatDateRange(action.dueDate, action.dueDate)}
                      </time>
                      <Tag bordered>Researcher action</Tag>
                    </Space>
                    <Typography.Title level={3}>{action.title}</Typography.Title>
                    <Typography.Paragraph>{action.details}</Typography.Paragraph>
                    <Typography.Paragraph type="secondary">
                      <Typography.Text strong>Why manual: </Typography.Text>
                      {action.whyManual}
                    </Typography.Paragraph>
                    {linkedWeekNumber ? (
                      <InternalLinkButton
                        href={"/weeks/" + linkedWeekNumber}
                        icon={<ArrowRightOutlined />}
                        iconPlacement="end"
                        type="link"
                      >
                        Tracked in Week {linkedWeekNumber}
                      </InternalLinkButton>
                    ) : null}
                  </Card>
                ),
                icon: <QuestionCircleOutlined />,
              };
            })}
          />
        ) : (
          <Empty description="No manual actions are recorded." image={Empty.PRESENTED_IMAGE_SIMPLE} />
        )}
      </section>

      <section className="protocol-section" aria-labelledby="decisions-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Already chosen</p>
            <h2 id="decisions-title">Locked decisions</h2>
          </div>
          <p>These choices stay fixed so later results cannot change the comparison.</p>
        </div>
        <Descriptions
          bordered
          className="protocol-descriptions"
          column={1}
          items={protocol.lockedDecisions.map((item) => ({
            key: item.label,
            label: item.label,
            children: item.value,
          }))}
        />
      </section>

      <section className="protocol-section" aria-labelledby="technical-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Reference detail</p>
            <h2 id="technical-title">Study design and analysis</h2>
          </div>
          <p>Open only the technical section you need. The recorded scientific content is unchanged.</p>
        </div>
        <Collapse
          className="protocol-collapse"
          defaultActiveKey={["analysis"]}
          items={[
            {
              key: "design",
              label: <h2 id="design-title">Experimental design</h2>,
              children: (
                <>
                  <Typography.Paragraph type="secondary">
                    The comparison changes the objective while holding the representation and
                    evaluation path fixed.
                  </Typography.Paragraph>
                  <Descriptions
                    bordered
                    column={1}
                    items={protocol.experimentalDesign.map((item) => ({
                      key: item.label,
                      label: item.label,
                      children: item.value,
                    }))}
                  />
                </>
              ),
            },
            {
              key: "corruptions",
              label: <h2 id="corruption-title">Corruption protocol</h2>,
              children: (
                <>
                  <Typography.Paragraph>{protocol.corruptionPrinciple}</Typography.Paragraph>
                  <Descriptions
                    bordered
                    column={1}
                    items={protocol.corruptions.map((item) => ({
                      key: item.label,
                      label: item.label,
                      children: item.value,
                    }))}
                  />
                </>
              ),
            },
            {
              key: "analysis",
              label: <h2 id="analysis-title">Primary analysis</h2>,
              children: (
                <>
                  <div className="formula-pair">
                    {[protocol.primaryFormula, protocol.effectFormula].map((formula) => (
                      <Typography.Text
                        key={formula}
                        style={{
                          background: "#000000",
                          borderRadius: 10,
                          color: "#ffffff",
                          display: "block",
                          fontFamily: '"SFMono-Regular", Consolas, "Liberation Mono", monospace',
                          overflowX: "auto",
                          padding: "12px 14px",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {formula}
                      </Typography.Text>
                    ))}
                  </div>
                  <div className="analysis-rule-list" role="list">
                    <Listy
                      itemRender={(rule, index) => (
                        <div role="listitem">
                        <Space align="start" size={12}>
                          <span className="decision-index">{index + 1}</span>
                          <span>{rule}</span>
                        </Space>
                        </div>
                      )}
                      items={protocol.analysisRules}
                      rowKey={(rule) => rule}
                    />
                  </div>
                </>
              ),
            },
            {
              key: "scope",
              label: <h2 id="scope-title">Scope and provenance</h2>,
              children: (
                <>
                  <Alert
                    description={protocol.bindingSource}
                    icon={<LockOutlined />}
                    title="Scope authority"
                    showIcon
                    type="info"
                  />
                  <Typography.Title id="exclusions-title" level={3}>
                    Outside this semester
                  </Typography.Title>
                  <div className="scope-exclusion-list" role="list">
                    <Listy
                      itemRender={(exclusion) => <div role="listitem">{exclusion}</div>}
                      items={protocol.scopeExclusions}
                      rowKey={(exclusion) => exclusion}
                    />
                  </div>
                </>
              ),
            },
          ]}
        />
      </section>
    </div>
  );
}
