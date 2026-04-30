import assert from "node:assert/strict";
import test from "node:test";

import { ApiError } from "../app/lib/api-client";
import {
  buildExpenseListFilters,
  generateMonthlyAdvice,
  getExpensePaginationState,
  getPlanResultRows,
  getUploadFailureMessage,
  validateExpenseForm,
  validatePlanForm,
} from "../app/lib/ui-logic";

test("ExpenseForm validation rejects invalid amount, note, and date", () => {
  assert.equal(
    validateExpenseForm({ amount: "0", note: "午餐", date: "2026-04-30" }),
    "金额非法，请输入大于 0 的数字"
  );
  assert.equal(
    validateExpenseForm({ amount: "12", note: "   ", date: "2026-04-30" }),
    "备注不能为空，请填写消费备注"
  );
  assert.equal(
    validateExpenseForm({ amount: "12", note: "午餐", date: "" }),
    "请选择消费日期"
  );
  assert.equal(
    validateExpenseForm({ amount: "12.5", note: "午餐", date: "2026-04-30" }),
    null
  );
});

test("ExpenseList builds filters and pagination state", () => {
  assert.deepEqual(
    buildExpenseListFilters({
      startDate: "2026-04-01",
      endDate: "",
      category: "餐饮",
      keyword: "",
      limit: 20,
      offset: 40,
    }),
    {
      startDate: "2026-04-01",
      endDate: undefined,
      category: "餐饮",
      keyword: undefined,
      limit: 20,
      offset: 40,
    }
  );

  assert.deepEqual(getExpensePaginationState({ total: 45, limit: 20, offset: 20 }), {
    totalPages: 3,
    currentPage: 2,
    canGoPrevious: true,
    canGoNext: true,
  });
  assert.equal(
    getExpensePaginationState({ total: 45, limit: 20, offset: 40 }).canGoNext,
    false
  );
});

test("PlanForm validation and result display rows match expected copy", () => {
  assert.equal(
    validatePlanForm({
      monthlyIncome: "",
      fixedExpenses: "1000",
      minimumLivingCost: "800",
      targetAmount: "5000",
      deadline: "2026-06-01",
    }),
    "月收入必须大于 0"
  );
  assert.equal(
    validatePlanForm({
      monthlyIncome: "3000",
      fixedExpenses: "1000",
      minimumLivingCost: "800",
      targetAmount: "5000",
      deadline: "2026-06-01",
    }),
    null
  );

  const rows = getPlanResultRows({
    remaining_days: 30,
    daily_saving: 50,
    monthly_available: 2000,
    daily_available: 40,
    target_amount: 1500,
    feasibility_score: 80,
    minimum_living_cost: 800,
    safe_saving_capacity: 1200,
    status: "hard",
    message: "目标较紧张",
  });

  assert.deepEqual(rows, [
    "剩余天数：30",
    "每日需存：50 元",
    "每月可支配：2000 元",
    "日均可支配：40 元",
    "可行性评分：80 / 100",
    "状态：hard",
    "说明：目标较紧张",
  ]);
});

test("BackupPanel upload failures prefer API error messages", () => {
  assert.equal(
    getUploadFailureMessage(new ApiError("备份文件校验失败", 400), "数据库恢复失败"),
    "备份文件校验失败"
  );
  assert.equal(getUploadFailureMessage(new Error("boom"), "CSV 导入失败"), "CSV 导入失败");
});

test("MonthlySummary returns empty-data advice", () => {
  assert.deepEqual(
    generateMonthlyAdvice({
      month: "2026-04",
      total_amount: 0,
      count: 0,
      average_daily_amount: 0,
      items: [],
    }),
    ["本月暂无消费记录。先记录几笔日常开销，系统会根据数据分析消费结构。"]
  );
});
