import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("journey connects all fourteen chapters to their working plans", async ({ page, isMobile }) => {
  await page.goto("/journey");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    /One example\.\s*A world\s*of motion\./,
  );
  await expect(page.locator("[data-scene-state]")).toHaveAttribute("data-scene-state", /ready|unavailable/);

  if (isMobile) await page.getByRole("button", { name: "Open navigation" }).click();
  await expect(page.getByRole("link", { name: "Journey", exact: true }).filter({ visible: true }))
    .toHaveAttribute("aria-current", "page");
  if (isMobile) await page.getByRole("link", { name: "Journey", exact: true }).filter({ visible: true }).click();

  const chapterHeadings = [];
  for (let week = 1; week <= 14; week += 1) {
    const chapter = page.locator(`#week-${week}`);
    await expect(chapter).toBeAttached();
    const heading = chapter.getByRole("heading").first();
    await expect(heading).toBeVisible();
    chapterHeadings.push(await heading.innerText());
    await expect(chapter.locator(`a[href="/weeks/${week}"]`)).toHaveCount(1);
    await expect(page.locator(`a[href="#week-${week}"]`).first()).toBeAttached();
  }
  expect(new Set(chapterHeadings).size).toBe(14);

  await page.locator('a[href="#week-12"]').first().click();
  await expect(page).toHaveURL(/#week-12$/);
  await expect(page.locator("#week-12")).toBeInViewport();
  await page.locator('#week-12 a[href="/weeks/12"]').click();
  await expect(page).toHaveURL(/\/weeks\/12$/);
});

test("journey demonstrations respond to keyboard controls", async ({ page, isMobile }) => {
  await page.goto("/journey");
  await expect(page.locator('[data-scene-state="ready"]')).toBeVisible();
  if (isMobile) await page.getByRole("button", { name: "Explore controls", exact: true }).click();
  const pause = page.getByRole("button", { name: "Pause animation", exact: true });
  await pause.focus();
  await pause.press("Space");
  await expect(page.getByRole("button", { name: "Play animation", exact: true })).toBeVisible();

  for (const name of ["Contextual", "SupCon", "Contrastive"]) {
    const recipe = page.getByRole("button", { name, exact: true });
    await recipe.focus();
    await recipe.press("Space");
    await expect(recipe).toHaveAttribute("aria-pressed", "true");
  }

  for (const name of ["Jitter", "Missing joints", "Missing frames"]) {
    const corruption = page.getByRole("button", { name, exact: true });
    await corruption.focus();
    await corruption.press("Space");
    await expect(corruption).toHaveAttribute("aria-pressed", "true");
  }
  const severity = page.getByRole("slider", { name: "Corruption severity", exact: true });
  await severity.focus();
  await severity.press("Home");
  const minimum = await severity.inputValue();
  await severity.press("ArrowRight");
  expect(Number(await severity.inputValue())).toBeGreaterThan(Number(minimum));

  const clean = page.getByRole("button", { name: "Clean", exact: true });
  await clean.click();
  await expect(clean).toHaveAttribute("aria-pressed", "true");
  await expect(severity).toBeDisabled();
  const rotate = page.getByRole("button", { name: "Rotate view", exact: true });
  await rotate.focus();
  await rotate.press("Space");
  await expect(rotate).toBeFocused();
});

test("journey can return from an interactive demonstration to the current chapter", async ({ page, isMobile }) => {
  await page.goto("/journey");
  await expect(page.locator('[data-scene-state="ready"]')).toBeVisible();
  await page.getByRole("link", { name: "Jump to Week 8", exact: true }).click();
  const caption = page.locator(".journey-scene-caption p");
  await expect(caption).toHaveText("Nine heads. One sealed test.");
  if (isMobile) await page.getByRole("button", { name: "Explore controls", exact: true }).click();
  await page.getByRole("button", { name: "Contrastive", exact: true }).click();
  await expect(caption).toHaveText("A shared space. Three recipes.");
  const resume = page.getByRole("button", { name: "Resume chapter view", exact: true });
  await resume.click();
  await expect(resume).toHaveCount(0);
  await expect(caption).toHaveText("Nine heads. One sealed test.");
});

test("journey restores a directly linked chapter after initial hydration and reload", async ({ page }) => {
  await page.goto("/journey#week-8");
  await expect(page.locator('[data-scene-state="ready"]')).toBeVisible();
  await expect(page.locator("#week-8")).toBeInViewport();
  await expect(page.locator(".journey-scene-caption p")).toHaveText("Nine heads. One sealed test.");

  await page.reload();
  await expect(page.locator('[data-scene-state="ready"]')).toBeVisible();
  await expect(page.locator("#week-8")).toBeInViewport();
  await expect(page.locator(".journey-scene-caption p")).toHaveText("Nine heads. One sealed test.");
});

test("journey remains readable without WebGL and honors reduced motion", async ({ page, isMobile }) => {
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.addInitScript(() => {
    const getContext = HTMLCanvasElement.prototype.getContext;
    Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
      value(this: HTMLCanvasElement, contextId: string, ...args: unknown[]) {
        if (contextId.includes("webgl")) return null;
        return Reflect.apply(getContext, this, [contextId, ...args]);
      },
    });
  });
  await page.goto("/journey");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(page.locator('[data-reduced-motion="true"]')).toBeVisible();
  await expect(page.locator('[data-scene-state="unavailable"]')).toBeVisible();
  if (isMobile) await page.getByRole("button", { name: "Explore controls", exact: true }).click();
  await expect(page.getByText("3D unavailable · static illustration", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Play animation", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Play animation", exact: true })).toBeDisabled();
  await expect(page.locator("#week-1").getByRole("heading").first()).toBeVisible();
  await expect(page.locator("#week-14").getByRole("heading").first()).toBeVisible();
  await page.locator('a[href="#week-14"]').first().click();
  await expect(page.locator("#week-14")).toBeInViewport();
  expect(pageErrors).toEqual([]);
});

test("journey fits the viewport throughout the story", async ({ page }) => {
  await page.goto("/journey");
  for (const selector of ["h1", "#week-1", "#week-5", "#week-9", "#week-14"]) {
    await page.locator(selector).scrollIntoViewIfNeeded();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1))
      .toBe(true);
  }
});

test("journey has no detectable WCAG A or AA violations", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/journey");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(page.locator('[data-reduced-motion="true"]')).toBeVisible();
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
});
