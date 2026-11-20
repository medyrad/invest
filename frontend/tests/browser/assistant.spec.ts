import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const evidence = process.env.INVEST_AI_EVIDENCE || path.resolve(__dirname, "../../../docs/stage9/evidence/browser");
const ids = ["11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222", "33333333-3333-3333-3333-333333333333"];

function success() {
  return {
    state: "completed",
    interpretation: { criteria: { kind: "project", route: "investor", budget_max: "30000000000" }, needs_clarification: false, questions: [] },
    answer: "سه نتیجه بر پایه نسخه عمومی و محاسبه سرور آماده است.",
    citations: ids.map((id, index) => ({ id, revision: `revision-${index}`, field: "matching" })),
    next: [], receipt: "synthetic-browser-receipt",
    quota: { used: 1, limit: 3, remaining: 2, reset_at: "2026-11-21T00:00:00Z", policy_version: 1, model: "gpt-6.2-sol" },
    server_result: { total: 3, next: null, policy_version: 1, items: ids.map((id, index) => ({ id, revision: `revision-${index}`, kind: "project", fields: { title: `فرصت مصنوعی ${["۱", "۲", "۳"][index]}` }, matching: { score: String(80 - index * 10), coverage: String(90 - index * 5), status: "ranked", checks: [], warnings: [], policy_version: 1 } })) },
  };
}

for (const width of [360, 390, 768, 1440]) test(`assistant complete journey remains usable at ${width}`, async ({ browser }) => {
  fs.mkdirSync(evidence, { recursive: true });
  const context = await browser.newContext({ viewport: { width, height: width < 768 ? 844 : 1000 }, reducedMotion: "reduce" });
  const page = await context.newPage();
  await page.route("**/api/v1/assistant/turns", (route) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(success()) }));
  await page.goto("/assistant");
  await page.evaluate(() => document.fonts.ready);
  const routePicker = page.getByRole("button", { name: "سرمایه‌گذاری" });
  await expect(routePicker).toBeVisible();
  await routePicker.focus();
  await expect(routePicker).toBeFocused();
  const hitTarget = await routePicker.evaluate((element) => {
    const box = element.getBoundingClientRect();
    const hit = document.elementFromPoint(box.left + box.width / 2, box.top + box.height / 2);
    return hit === element || element.contains(hit);
  });
  expect(hitTarget).toBe(true);
  await routePicker.press("Enter");
  await expect(routePicker).toHaveAttribute("aria-pressed", "true");
  await page.screenshot({ path: path.join(evidence, `assistant-initial-${width}.png`), fullPage: true, animations: "disabled" });
  await page.getByLabel("شرایط شما برای دستیار").fill("پروژه تهران تا ۳۰ میلیارد تومان");
  await page.getByLabel("شرایط شما برای دستیار").press("Enter");
  await expect(page.getByRole("heading", { name: "برداشت قابل اصلاح" })).toBeVisible();
  await expect(page.getByText("فرصت مصنوعی ۱", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "ادامه با فیلتر دستی" })).toBeVisible();
  await expect(page.getByRole("button", { name: "ذخیره با رسید سرور" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  await page.screenshot({ path: path.join(evidence, `assistant-complete-${width}.png`), fullPage: true, animations: "disabled" });
  await context.close();
});

test("assistant outage preserves text, criteria and manual continuation without false success", async ({ page }) => {
  const value = success();
  await page.route("**/api/v1/assistant/turns", (route) => route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ ...value, state: "failed", answer: undefined, error: { code: "provider_unavailable", message: "دستیار متصل در دسترس نیست؛ مسیر دستی آماده است." } }) }));
  await page.goto("/assistant");
  await page.getByLabel("شرایط شما برای دستیار").fill("پروژه تهران تا ۳۰ میلیارد تومان");
  await page.getByRole("button", { name: "ارسال برای بررسی" }).click();
  await expect(page.getByText("موفقیت ثبت نشده است.")).toBeVisible();
  await expect(page.getByText("سقف بودجه:")).toBeVisible();
  await expect(page.getByRole("button", { name: "ادامه با فیلتر دستی" })).toBeEnabled();
});

test("home handoff keeps private text out of URL", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("شرایط شما برای دستیار").fill("متن مصنوعی حساس برای نشست");
  await page.getByRole("button", { name: "پیشنهاد بگیرید" }).click();
  await expect(page).toHaveURL(/\/assistant$/);
  await expect(page.getByLabel("شرایط شما برای دستیار")).toHaveValue("متن مصنوعی حساس برای نشست");
  expect(page.url()).not.toContain("متن");
});

test("@desktop comparison chat revalidates a same-kind selection and renders a grounded reply", async ({ page }) => {
  await page.goto("/assistant");
  const feed = await page.evaluate(async () => {
    const response = await fetch("/api/v1/core/opportunities?criteria=%7B%7D", { cache: "no-store" });
    if (!response.ok) throw new Error(`feed:${response.status}`);
    return response.json() as Promise<{ items: Array<{ id: string; revision: string; kind: string }> }>;
  });
  const groups = feed.items.reduce<Record<string, typeof feed.items>>((current, item) => {
    (current[item.kind] ||= []).push(item);
    return current;
  }, {});
  const pair = Object.values(groups).find((items) => items.length >= 2)?.slice(0, 2);
  expect(pair?.length).toBe(2);
  await page.route("**/api/v1/assistant/turns", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({
      state: "completed",
      answer: "تفاوت‌ها فقط از ردیف‌های عمومی همین دو نسخه توضیح داده شد.",
      citations: pair!.map((item) => ({ id: item.id, revision: item.revision, field: "matching" })),
      next: [],
      receipt: "synthetic-compare-receipt",
      quota: { used: 1, limit: 3, remaining: 2 },
    }),
  }));
  await page.goto(`/compare?ids=${pair!.map((item) => item.id).join(",")}`);
  await expect(page.getByText("۲ از ۴ فرصت", { exact: false })).toBeVisible({ timeout: 20_000 });
  await page.getByLabel("پرسش درباره مقایسه").fill("تفاوت مهم این دو مورد چیست؟");
  await page.getByRole("button", { name: "پرسیدن درباره جدول" }).click();
  await expect(page.getByText("تفاوت‌ها فقط از ردیف‌های عمومی همین دو نسخه توضیح داده شد.")).toBeVisible();
  await expect(page.getByText("۲ استناد به نسخه عمومی")).toBeVisible();
});
