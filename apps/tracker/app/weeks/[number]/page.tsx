import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import Loading from "@/app/loading";
import { getRequestPublicPlan } from "@/lib/request-plan";
import { WeekDetailView } from "./week-detail-view";

type WeekPageProps = { params: Promise<{ number: string }> };

export async function generateStaticParams() {
  return Array.from({ length: 14 }, (_, index) => ({ number: String(index + 1) }));
}

export async function generateMetadata({ params }: WeekPageProps): Promise<Metadata> {
  const { number } = await params;
  const plan = await getRequestPublicPlan();
  const week = plan.weeks.find((candidate) => candidate.number === Number(number));
  if (!week) notFound();
  return { title: `Week ${week.number}: ${week.title}` };
}

export default function WeekPage(props: WeekPageProps) {
  return (
    <Suspense fallback={<Loading />}>
      <WeekPageContent {...props} />
    </Suspense>
  );
}

async function WeekPageContent({ params }: WeekPageProps) {
  const { number } = await params;
  const plan = await getRequestPublicPlan();
  const week = plan.weeks.find((candidate) => candidate.number === Number(number));
  if (!week) notFound();

  const weeks = plan.weeks.filter(
    (candidate) => Math.abs(candidate.number - week.number) <= 1,
  );
  const weekSources = plan.weekSources.filter((link) => link.weekId === week.id);
  const sourceIds = new Set(weekSources.map((link) => link.sourceId));

  return (
    <WeekDetailView
      plan={{
        dataSource: plan.dataSource,
        lastRefreshedAt: plan.lastRefreshedAt,
        project: { timezone: plan.project.timezone },
        sources: plan.sources.filter((source) => sourceIds.has(source.id)),
        weeks,
        weekSources,
      }}
      weekNumber={week.number}
    />
  );
}
