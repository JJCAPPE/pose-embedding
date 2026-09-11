import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("public dashboard exposes all published weeks", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("protocol lock");
  await expect(page.getByRole("heading", { name: "Recent completions" })).toBeVisible();
  await expect(page.getByText("No tasks are complete yet.", { exact: false })).toBeVisible();
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

test("week details show tasks, gates, risks, and advisor checkpoint", async ({ page }) => {
  await page.goto("/weeks/5");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Corruption freeze");
  await expect(page.getByText("5h planned", { exact: true })).toBeVisible();
  await expect(page.getByText("0h actual", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Close Week 4 before starting." })).toBeVisible();
  await expect(page.getByRole("link", { name: /Week 4: Heads, losses, and sampler/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Work for the week" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Advance when" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Watch closely" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Advisor checkpoint" })).toBeVisible();
});

test("first week always shows its protocol prerequisites", async ({ page }) => {
  await page.goto("/weeks/1");
  await expect(page.getByRole("heading", { name: "Begin from the locked protocol." })).toBeVisible();
  await expect(page.getByRole("link", { name: "Review manual actions" })).toHaveAttribute(
    "href",
    "/protocol#manual-actions",
  );
});

test("protocol preserves locked decisions and manual actions", async ({ page }) => {
  await page.goto("/protocol");
  await expect(page.getByRole("heading", { name: "The rules before the result." })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Actions only you can complete" })).toBeVisible();
  await expect(page.getByText("Contrastive-only, supervised contrastive, and full contextual-plus-contrastive.")).toBeVisible();
  await expect(page.getByText("drop(m, s, c)", { exact: false })).toBeVisible();
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
  await expect(page.getByText("Development split", { exact: true })).toBeVisible();
  await expect(page.getByText("Coordinate jitter", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Outside this semester" })).toBeVisible();

  await page.goto("/weeks/5");
  await expect(page.getByRole("heading", { name: "Corruption freeze" })).toBeVisible();
  await expect(page.locator("#task-w05-task-04")).toBeVisible();
  await expect(page.getByText("Fixed coordinate noise may not be comparable across body scales.")).toBeVisible();
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
