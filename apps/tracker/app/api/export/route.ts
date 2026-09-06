import { getPublicPlan } from "@/lib/data";
import { planToMarkdown } from "@/lib/export";
import { publicPlan } from "@/lib/domain";

export async function GET(request: Request) {
  const plan = publicPlan(await getPublicPlan());
  const format = new URL(request.url).searchParams.get("format") ?? "json";

  if (format === "markdown") {
    return new Response(planToMarkdown(plan), {
      headers: {
        "Content-Disposition": "attachment; filename=pose-embed-plan.md",
        "Content-Type": "text/markdown; charset=utf-8",
        "Cache-Control": "public, s-maxage=300, stale-while-revalidate=3600",
      },
    });
  }

  if (format !== "json") {
    return Response.json(
      { error: "Unsupported format. Use json or markdown." },
      { status: 400 },
    );
  }

  return new Response(`${JSON.stringify(plan, null, 2)}\n`, {
    headers: {
      "Content-Disposition": "attachment; filename=pose-embed-plan.json",
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "public, s-maxage=300, stale-while-revalidate=3600",
    },
  });
}
