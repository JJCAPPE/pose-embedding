import type { Metadata } from "next";
import { Suspense } from "react";
import Loading from "@/app/loading";
import { getRequestPublicPlan } from "@/lib/request-plan";
import { LiteratureView } from "./literature-view";

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
  return (
    <LiteratureView
      plan={{
        dataSource: plan.dataSource,
        lastRefreshedAt: plan.lastRefreshedAt,
        sources: plan.sources,
        weeks: plan.weeks.map(({ id, number, state, title }) => ({
          id,
          number,
          state,
          title,
        })),
        weekSources: plan.weekSources,
      }}
    />
  );
}
