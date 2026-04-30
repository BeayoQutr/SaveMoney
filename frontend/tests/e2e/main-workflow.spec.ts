import { expect, test } from "@playwright/test";

test.skip(
  process.env.RUN_E2E !== "1",
  "Set RUN_E2E=1 and start backend/frontend services to run E2E tests."
);

test("main workflow shell is visible", async ({ page }) => {
  await page.goto(process.env.FRONTEND_URL ?? "http://127.0.0.1:3000");

  await expect(page.getByRole("heading", { name: "记一笔消费" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "攒钱计划" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "本月总览与统计" })).toBeVisible();
});
