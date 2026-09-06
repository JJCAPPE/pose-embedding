import type { Metadata } from "next";
import { Suspense } from "react";
import Loading from "@/app/loading";
import { DataNotice } from "@/components/data-notice";
import { getRequestPublicPlan } from "@/lib/request-plan";

export const metadata: Metadata = { title: "Literature" };
export default function LiteraturePage() {
  return (
    <Suspense fallback={<Loading />}>
      <LiteraturePageContent />
    </Suspense>
  );
}

async function LiteraturePageContent() {
  const plan = await getRequestPublicPlan();
  const usageBySource = new Map(
    plan.sources.map((source) => [
      source.id,
      plan.weekSources.filter((link) => link.sourceId === source.id),
    ]),
  );

  return (
    <div className="shell page-shell">
      <DataNotice plan={plan} />
      <header className="page-header">
        <p className="eyebrow">Evidence ledger</p>
        <h1>Literature with a job to do.</h1>
        <p>
          Every source is tied to a protocol choice, implementation check, or reporting constraint.
        </p>
      </header>

      <section className="literature-layout" aria-label="Verified sources">
        {plan.sources.map((source) => {
          const usages = usageBySource.get(source.id) ?? [];
          return (
            <article className="source-card" key={source.id}>
              <div className="source-year">{source.year}</div>
              <div>
                <h2>
                  <a href={source.canonicalUrl} rel="noreferrer" target="_blank">
                    {source.title}
                  </a>
                </h2>
                <p className="source-authors">{source.authors}</p>
                <p>{source.purpose}</p>
                <div className="source-usage">
                  <strong>Used in</strong>
                  {usages.length > 0 ? (
                    <span>{usages.map((usage) => `Week ${Number(usage.weekId.slice(-2))}`).join(", ")}</span>
                  ) : (
                    <span>Project-wide reference</span>
                  )}
                </div>
                <small>Link verified {source.verifiedAt}</small>
              </div>
            </article>
          );
        })}
      </section>
    </div>
  );
}
