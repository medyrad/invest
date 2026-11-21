import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const evidence = process.env.INVEST_AI_EVIDENCE;
const publicSeed = [
  ["توسعه مسکن اجاره‌ای", "تهران", "residential", "22"],
  ["مرکز فرهنگی با خرید خدمت قراردادی", "تهران", "cultural", "14"],
  ["ساختمان اداری برای خریدار خدمت عمومی", "تهران", "office", "28"],
  ["توسعه مجموعه مسکونی", "فارس", "residential", "15"],
  ["توسعه مجموعه خدماتی مشترک", "تهران", "commercial", "12"],
  ["مشارکت در شبکه آب، فاضلاب و آب‌های سطحی", "تهران", "waternetwork", "18"],
  ["مشارکت در مرمت بناهای تاریخی", "تهران", "restoration", "20"],
  ["احداث مبلمان شهری در تهران", "تهران", "furniture", "21"],
] as const;
const ids = Array.from(
  { length: 8 },
  (_, index) =>
    `${String(index + 1).repeat(8)}-${String(index + 1).repeat(4)}-${String(index + 1).repeat(4)}-${String(index + 1).repeat(4)}-${String(index + 1).repeat(12)}`,
);

function success() {
  return {
    state: "completed",
    interpretation: {
      criteria: {
        kind: "project",
        route: "investor",
        budget_max: "30000000000",
      },
      needs_clarification: false,
      questions: [],
    },
    answer: "هشت نتیجه بر پایه نسخه عمومی و محاسبه سرور آماده است.",
    steps: [
      {
        id: "interpretation",
        status: "completed",
        detail: "شرط‌ها برداشت شدند.",
      },
      {
        id: "public_data",
        status: "completed",
        detail: "داده عمومی بازخوانی شد.",
      },
      {
        id: "explanation",
        status: "completed",
        detail: "توضیح اعتبارسنجی شد.",
      },
    ],
    citations: ids.map((id, index) => ({
      id,
      revision: `revision-${index}`,
      field: "matching",
    })),
    next: [],
    receipt: "deterministic-public-seed-receipt",
    quota: {
      used: 1,
      limit: 3,
      remaining: 2,
      reset_at: "2026-11-21T00:00:00Z",
      policy_version: 1,
      model: "gpt-6.2-sol",
    },
    server_result: {
      total: 8,
      next: null,
      policy_version: 1,
      items: ids.map((id, index) => ({
        id,
        revision: `revision-${index}`,
        kind: "project",
        fields: {
          title: publicSeed[index][0],
          province: publicSeed[index][1],
          city: publicSeed[index][1],
          subtype: publicSeed[index][2],
          minimum_investment: {
            status: "known",
            source_value: publicSeed[index][3],
            unit: { code: "BILLION_TOMAN", version: 1 },
          },
          image_url: `/images/types/${publicSeed[index][2]}.webp`,
        },
        matching: {
          score: String(95 - index * 5),
          coverage: String(90 - index * 3),
          status: "ranked",
          checks: [
            { axis: "مبلغ در بازه شما", state: "met", reason: "server" },
            { axis: "گروه پروژه", state: "met", reason: "server" },
            { axis: "استان", state: "met", reason: "server" },
          ],
          warnings: [],
          policy_version: 1,
        },
      })),
    },
  };
}

function stream(
  value: ReturnType<typeof success> & {
    error?: { code: string; message: string };
  } = success(),
) {
  return (
    [
      {
        event: "progress",
        stage: "interpretation",
        status: "active",
        detail: "متن در حال اعتبارسنجی است.",
      },
      {
        event: "progress",
        stage: "interpretation",
        status: "completed",
        detail: "شرط‌ها برداشت شدند.",
      },
      {
        event: "progress",
        stage: "public_data",
        status: "active",
        detail: "نسخه عمومی بازخوانی می‌شود.",
      },
      {
        event: "progress",
        stage: "public_data",
        status: "completed",
        detail: "سه مورد آماده شد.",
      },
      {
        event: "progress",
        stage: "explanation",
        status: "active",
        detail: "توضیح در حال اعتبارسنجی است.",
      },
      { event: value.state === "failed" ? "failure" : "result", data: value },
    ]
      .map((event) => JSON.stringify(event))
      .join("\n") + "\n"
  );
}

async function installStreamingTransport(
  page: import("@playwright/test").Page,
  value = success(),
) {
  const events = stream(value)
    .trim()
    .split("\n")
    .map((line) => JSON.parse(line));
  await page.addInitScript((payload) => {
    const original = window.fetch.bind(window);
    window.fetch = async (input, init) => {
      const url =
        typeof input === "string"
          ? input
          : input instanceof URL
            ? input.href
            : input.url;
      if (!url.includes("/api/v1/assistant/turns/stream"))
        return original(input, init);
      const encoder = new TextEncoder();
      const body = new ReadableStream({
        async start(controller) {
          const delays = [40, 120, 120, 120, 120, 900];
          for (let index = 0; index < payload.length; index += 1) {
            await new Promise((resolve) => setTimeout(resolve, delays[index]));
            controller.enqueue(
              encoder.encode(JSON.stringify(payload[index]) + "\n"),
            );
          }
          controller.close();
        },
      });
      return new Response(body, {
        status: 200,
        headers: { "Content-Type": "application/x-ndjson" },
      });
    };
  }, events);
}

test("assistant complete journey remains usable at the project viewport", async ({
  page,
}) => {
  const width = page.viewportSize()?.width || 1440;
  if (evidence) fs.mkdirSync(evidence, { recursive: true });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await installStreamingTransport(page);
  await page.goto("/assistant");
  await page.evaluate(() => document.fonts.ready);
  const composer = page.getByLabel("شرایط شما برای دستیار");
  await expect(composer).toBeVisible();
  await composer.focus();
  await expect(composer).toBeFocused();
  const hitTarget = await composer.evaluate((element) => {
    const box = element.getBoundingClientRect();
    const hit = document.elementFromPoint(
      box.left + box.width / 2,
      box.top + box.height / 2,
    );
    return hit === element || element.contains(hit);
  });
  expect(hitTarget).toBe(true);
  const finalExample = page
    .getByRole("button", { name: /مرمت خانه تاریخی در کاشان/ })
    .first();
  await finalExample.scrollIntoViewIfNeeded();
  await expect(finalExample).toBeVisible();
  await page.evaluate(() => scrollTo({ top: 0, behavior: "instant" }));
  await page
    .getByLabel("شرایط شما برای دستیار")
    .fill("پروژه تهران تا ۳۰ میلیارد تومان");
  await page.getByLabel("شرایط شما برای دستیار").press("Enter");
  await expect(
    page.getByRole("heading", { name: "در حال بررسی..." }),
  ).toBeVisible();
  await expect(page.getByText("شرط‌ها برداشت شدند.")).toBeVisible();
  await expect(page.getByText("سه مورد آماده شد.")).toBeVisible();
  await expect(page.getByText("توضیح در حال اعتبارسنجی است.")).toBeVisible();
  if (evidence)
    await page.screenshot({
      path: path.join(evidence, `product-processing-${width}.png`),
      animations: "disabled",
    });
  await expect(
    page.getByRole("heading", { name: "برداشت من از درخواست شما" }),
  ).toBeVisible();
  await expect(
    page
      .locator("span.inline-flex")
      .filter({ hasText: "مسیر:" })
      .filter({ hasText: "سرمایه‌گذاری و مشارکت" }),
  ).toBeVisible();
  await expect(
    page
      .locator("span.inline-flex")
      .filter({ hasText: "نوع:" })
      .filter({ hasText: "پروژه" }),
  ).toBeVisible();
  await expect(page.getByText(/پیشنهاد [123]/)).toHaveCount(3);
  await expect(page.getByText("investor", { exact: true })).toHaveCount(0);
  await expect(page.getByText("project", { exact: true })).toHaveCount(0);
  await expect(page.getByText(/revision-/)).toHaveCount(0);
  await expect(
    page.getByText("توسعه مسکن اجاره‌ای", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("احداث مبلمان شهری در تهران", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "دقیق‌تر کردن با فیلترها" }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "ذخیره شرایط" })).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBe(true);
  await page
    .locator("article")
    .filter({ hasText: "پیشنهاد ۱" })
    .first()
    .scrollIntoViewIfNeeded();
  if (evidence)
    await page.screenshot({
      path: path.join(evidence, `product-results-top-${width}.png`),
      animations: "disabled",
    });
});

test("assistant outage preserves text, criteria and manual continuation without false success", async ({
  page,
}) => {
  const value = success();
  await page.route("**/api/v1/assistant/turns/stream", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/x-ndjson",
      body: stream({
        ...value,
        state: "failed",
        answer: "",
        error: {
          code: "provider_unavailable",
          message: "دستیار متصل در دسترس نیست؛ مسیر دستی آماده است.",
        },
      }),
    }),
  );
  await page.goto("/assistant");
  await page
    .getByLabel("شرایط شما برای دستیار")
    .fill("پروژه تهران تا ۳۰ میلیارد تومان");
  await page.getByRole("button", { name: "ارسال برای بررسی" }).click();
  await expect(page.getByText("موفقیت ثبت نشده است.")).toBeVisible();
  await expect(page.getByText("سقف بودجه:")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "دقیق‌تر کردن با فیلترها" }),
  ).toBeEnabled();
});

test("home handoff keeps private text out of URL", async ({ page }) => {
  await page.goto("/");
  await page
    .getByLabel("شرایط شما برای دستیار")
    .fill("متن مصنوعی حساس برای نشست");
  await page.getByRole("button", { name: "پیشنهاد بگیرید" }).click();
  await expect(page).toHaveURL(/\/assistant$/);
  await expect(page.getByLabel("شرایط شما برای دستیار")).toHaveValue(
    "متن مصنوعی حساس برای نشست",
  );
  expect(page.url()).not.toContain("متن");
});

test("@desktop comparison chat revalidates a same-kind selection and renders a grounded reply", async ({
  page,
}) => {
  await page.goto("/assistant");
  const feed = await page.evaluate(async () => {
    const response = await fetch("/api/v1/core/opportunities?criteria=%7B%7D", {
      cache: "no-store",
    });
    if (!response.ok) throw new Error(`feed:${response.status}`);
    return response.json() as Promise<{
      items: Array<{ id: string; revision: string; kind: string }>;
    }>;
  });
  const groups = feed.items.reduce<Record<string, typeof feed.items>>(
    (current, item) => {
      (current[item.kind] ||= []).push(item);
      return current;
    },
    {},
  );
  const pair = Object.values(groups)
    .find((items) => items.length >= 2)
    ?.slice(0, 2);
  expect(pair?.length).toBe(2);
  await page.route("**/api/v1/assistant/turns", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        state: "completed",
        answer: "تفاوت‌ها فقط از ردیف‌های عمومی همین دو نسخه توضیح داده شد.",
        citations: pair!.map((item) => ({
          id: item.id,
          revision: item.revision,
          field: "matching",
        })),
        next: [],
        receipt: "synthetic-compare-receipt",
        quota: { used: 1, limit: 3, remaining: 2 },
      }),
    }),
  );
  await page.goto(`/compare?ids=${pair!.map((item) => item.id).join(",")}`);
  await expect(page.getByText("۲ از ۴ فرصت", { exact: false })).toBeVisible({
    timeout: 20_000,
  });
  await page
    .getByLabel("پرسش درباره مقایسه")
    .fill("تفاوت مهم این دو مورد چیست؟");
  await page.getByRole("button", { name: "پرسیدن درباره جدول" }).click();
  await expect(
    page.getByText(
      "تفاوت‌ها فقط از ردیف‌های عمومی همین دو نسخه توضیح داده شد.",
    ),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "نتیجه تطبیق سرور" }),
  ).toHaveCount(2);
});
