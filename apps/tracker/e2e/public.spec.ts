import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFileSync } from "node:fs";
import { recentCompletedTasks } from "../lib/domain";
import type { ResearchPlan } from "../lib/schema";

const seedPlan: ResearchPlan = JSON.parse(
  readFileSync(new URL("../../../plan/research-plan.v3.json", import.meta.url), "utf8"),
);

test("public dashboard exposes all published weeks", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("protocol lock");
  await expect(page.getByRole("heading", { name: "Unblock Week 1: Protocol and access" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Recent completions" })).toBeVisible();
  for (const { task } of recentCompletedTasks(seedPlan)) {
    await expect(page.getByRole("heading", { name: task.title, exact: true })).toBeVisible();
  }
  await expect(page.getByRole("list", { name: undefined }).last().getByRole("listitem")).toHaveCount(14);
});

test("an unavailable configured database falls back to the visible plan snapshot", async ({
  page,
  request,
}) => {
  const healthResponse = await request.get("/api/health");
  const health = await healthResponse.json();
  test.skip(health.dataSource !== "seed", "This deployment has a reachable live database.");

  await page.goto("/");
  await expect(page.getByRole("status")).toContainText("Viewing saved snapshot");
  await expect(page.getByRole("list", { name: undefined }).last().getByRole("listitem")).toHaveCount(14);
});

test("week details show tasks, gates, risks, and research checkpoint", async ({ page }) => {
  await page.goto("/weeks/5");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(seedPlan.weeks[4].title);
  await expect(page.getByText("5h planned", { exact: true })).toBeVisible();
  await expect(page.getByText("No time recorded", { exact: true })).toBeVisible();
  await expect(page.getByText("Prerequisites ready", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Close Week 4 before starting." })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Work for the week" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Advance when" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Watch closely" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Research checkpoint" })).toBeVisible();
});

test("first week always shows its protocol prerequisites", async ({ page }) => {
  await page.goto("/weeks/1");
  await expect(page.getByText("No prior-week dependency", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Begin from the locked protocol." })).toBeVisible();
  await expect(page.getByRole("link", { name: "Review manual actions" })).toHaveAttribute(
    "href",
    "/protocol#manual-actions",
  );
});

test("protocol publishes the v3 planning direction and pending capacity gate", async ({ page }) => {
  await page.goto("/protocol");
  await expect(page.getByRole("heading", { name: "The rules before the result." })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Actions only you can complete" })).toBeVisible();
  await expect(page.getByText("Capacity is a gate, not a completed result")).toBeVisible();
  await expect(page.getByText(/100 GB of incremental storage/)).toBeVisible();
  await expect(page.getByText(/7, 17, 29/).first()).toBeVisible();
  await expect(page.getByRole("link", { name: "Read the final v3 plan" })).toHaveAttribute("href", "/protocol/plan");
  await expect(page.getByText("26 declared configurations:", { exact: false })).toHaveCount(0);
});

test("final plan and scope decision are readable and downloadable", async ({ page, request }) => {
  await page.goto("/protocol/plan");
  await expect(page.getByRole("heading", { level: 1, name: "Final v3 plan: frozen one-shot pose robustness" })).toBeVisible();
  await expect(page.getByRole("table").first()).toBeVisible();
  await expect(page.getByRole("link", { name: "Capacity gates", exact: true })).toHaveAttribute("href", "#8-capacity-gates");
  await page.getByRole("link", { name: "Scope decision", exact: true }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Return the December study");
  const download = await request.get("/protocol/plan/source");
  expect(download.headers()["content-type"]).toContain("text/markdown");
  expect(await download.text()).toContain("100 GB");
  expect((await request.get("/protocol/private/source")).status()).toBe(404);
});

test("protocol formula scrollers are keyboard accessible", async ({ page }) => {
  await page.goto("/protocol");
  await expect(page.getByRole("heading", { name: "The rules before the result." })).toBeVisible();
  await expect(page.locator(".formula-pair [tabindex='0']")).toHaveCount(2);

  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
});

test("print output includes collapsed protocol and weekly detail", async ({ page }) => {
  await page.emulateMedia({ media: "print" });
  await page.goto("/protocol");
  await expect(page.getByRole("heading", { name: "The rules before the result." })).toBeVisible();
  await expect(page.getByText(seedPlan.protocol.experimentalDesign[0].label, { exact: true })).toBeVisible();
  await expect(page.getByText("Coordinate jitter", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Outside this semester" })).toBeVisible();

  await page.goto("/weeks/5");
  await expect(page.getByRole("heading", { name: seedPlan.weeks[4].title })).toBeVisible();
  await expect(page.locator("#task-w05-task-04")).toBeVisible();
  await expect(page.getByText(seedPlan.weeks[4].risks[0], { exact: true })).toBeVisible();
});

test("public exports and health endpoint report their current data source", async ({ request }) => {
  const exportResponse = await request.get("/api/export?format=json");
  expect(exportResponse.ok()).toBe(true);
  const plan = await exportResponse.json();
  expect(plan.weeks).toHaveLength(14);
  expect(["seed", "supabase"]).toContain(plan.dataSource);

  const healthResponse = await request.get("/api/health");
  expect(healthResponse.ok()).toBe(true);
  const health = await healthResponse.json();
  expect(health.dataSource).toBe(plan.dataSource);
  expect(health.status).toBe(plan.dataSource === "supabase" ? "ok" : "degraded");
  expect(typeof health.editingEnabled).toBe("boolean");
});

test("invalid week renders a useful not-found state", async ({ page }) => {
  await page.goto("/weeks/15");
  await expect(page.getByRole("heading", { name: "Page not found" })).toBeVisible();
  await expect(page.locator('meta[name="robots"]').first()).toHaveAttribute("content", /noindex/);
});

test("public dashboard has no detectable WCAG A or AA violations", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
});
