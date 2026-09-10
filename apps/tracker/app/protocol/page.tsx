import type { Metadata } from "next";
import { Suspense } from "react";
import Loading from "@/app/loading";
import { getRequestPublicPlan } from "@/lib/request-plan";
import { ProtocolView } from "./protocol-view";

export const metadata: Metadata = { title: "Protocol" };

export default function ProtocolPage() {
  return (
    <Suspense fallback={<Loading />}>
      <ProtocolPageContent />
    </Suspense>
  );
}

async function ProtocolPageContent() {
  const plan = await getRequestPublicPlan();
  const weekNumberByTaskId = Object.fromEntries(
    plan.weeks.flatMap((week) => week.tasks.map((task) => [task.id, week.number])),
  );

  return (
    <ProtocolView
      dataSource={plan.dataSource}
      lastRefreshedAt={plan.lastRefreshedAt}
      manualActions={plan.manualActions}
      protocol={plan.protocol}
      weekNumberByTaskId={weekNumberByTaskId}
    />
  );
}
