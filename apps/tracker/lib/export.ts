import type { LoadedPlan } from "@/lib/schema";
import { formatDateRange, projectProgress, weekCanClose } from "@/lib/domain";

export function planToMarkdown(plan: LoadedPlan): string {
  const progress = projectProgress(plan);
  const lines = [
    `# ${plan.project.title}`,
    "",
    plan.project.summary,
    "",
    `**Research question:** ${plan.project.researchQuestion}`,
    "",
    `**Schedule:** ${plan.project.startDate} to ${plan.project.endDate}`,
    `**Required-task progress:** ${progress.completedRequiredTasks}/${progress.requiredTasks} (${progress.percent}%)`,
    `**Data source:** ${plan.dataSource}`,
    "",
    "## Protocol",
    "",
    plan.protocol.successDefinition,
    "",
    `**Binding source:** ${plan.protocol.bindingSource}`,
    "",
    "### Locked decisions",
    "",
    ...plan.protocol.lockedDecisions.map((item) => `- **${item.label}:** ${item.value}`),
    "",
    "### Experimental design",
    "",
    ...plan.protocol.experimentalDesign.map((item) => `- **${item.label}:** ${item.value}`),
    "",
    "### Corruptions",
    "",
    plan.protocol.corruptionPrinciple,
    "",
    ...plan.protocol.corruptions.map((item) => `- **${item.label}:** ${item.value}`),
    "",
    "### Primary analysis",
    "",
    `\`${plan.protocol.primaryFormula}\``,
    "",
    `\`${plan.protocol.effectFormula}\``,
    "",
    ...plan.protocol.analysisRules.map((rule) => `- ${rule}`),
    "",
    "### Manual actions",
    "",
    ...plan.manualActions.map(
      (action) => `- **By ${action.dueDate}, ${action.title}:** ${action.details}`,
    ),
    "",
  ];

  for (const week of plan.weeks) {
    lines.push(
      `## Week ${week.number}: ${week.title}`,
      "",
      `**Dates:** ${formatDateRange(week.startDate, week.endDate)}  `,
      `**Phase:** ${week.phase}  `,
      `**Budget:** ${week.plannedMinutes / 60} hours planned, ${(week.actualMinutes / 60).toFixed(1)} hours actual  `,
      `**State:** ${week.state}  `,
      `**Ready to close:** ${weekCanClose(week) ? "yes" : "no"}`,
      "",
      week.objective,
      "",
      `**Deliverable:** ${week.deliverable}`,
      "",
      "### Tasks",
      "",
    );

    for (const task of week.tasks) {
      const marker = task.state === "done" ? "x" : " ";
      const optional = task.required ? "" : " (optional)";
      lines.push(`- [${marker}] ${task.title}${optional}: ${task.expectedOutput}`);
    }

    lines.push("", "### Advancement gates", "");
    for (const gate of week.gates) {
      lines.push(`- **${gate.state}:** ${gate.criterion}`);
    }

    lines.push("", "### Risks", "");
    for (const risk of week.risks) lines.push(`- ${risk}`);
    lines.push("", `**Advisor prompt:** ${week.advisorPrompt}`, "");
  }

  lines.push("## Literature", "");
  for (const source of plan.sources) {
    lines.push(
      `- [${source.title}](${source.canonicalUrl}) (${source.authors}, ${source.year}): ${source.purpose}`,
    );
  }

  return `${lines.join("\n").trim()}\n`;
}
