import {
  CategoryItem,
  ExpenseListResponse,
  MonthlySummary,
  PlanResult,
} from "../types";
import { ApiError } from "./api-client";

export type ExpenseValidationInput = {
  amount: string;
  note: string;
  date: string;
};

export function validateExpenseForm(input: ExpenseValidationInput): string | null {
  const amountNum = Number(input.amount);
  if (!input.amount || Number.isNaN(amountNum) || amountNum <= 0) {
    return "金额非法，请输入大于 0 的数字";
  }
  if (!input.note.trim()) {
    return "备注不能为空，请填写消费备注";
  }
  if (!input.date) {
    return "请选择消费日期";
  }
  return null;
}

export type PlanValidationInput = {
  monthlyIncome: string;
  fixedExpenses: string;
  minimumLivingCost: string;
  targetAmount: string;
  deadline: string;
};

export function validatePlanForm(input: PlanValidationInput): string | null {
  const income = Number(input.monthlyIncome);
  const fixed = Number(input.fixedExpenses);
  const target = Number(input.targetAmount);
  const minimum = Number(input.minimumLivingCost);

  if (!income || income <= 0) {
    return "月收入必须大于 0";
  }
  if (fixed < 0 || minimum < 0) {
    return "固定支出和最低生活费不能小于 0";
  }
  if (!target || target <= 0) {
    return "攒钱目标必须大于 0";
  }
  if (!input.deadline) {
    return "请选择截止日期";
  }
  return null;
}

export function getPlanResultRows(result: PlanResult) {
  return [
    `剩余天数：${result.remaining_days}`,
    `每日需存：${result.daily_saving} 元`,
    `每月可支配：${result.monthly_available} 元`,
    `日均可支配：${result.daily_available} 元`,
    `可行性评分：${result.feasibility_score} / 100`,
    `状态：${result.status}`,
    `说明：${result.message}`,
  ];
}

export type ExpenseFilterState = {
  startDate: string;
  endDate: string;
  category: string;
  keyword: string;
  limit: number;
  offset: number;
};

export function buildExpenseListFilters(filters: ExpenseFilterState) {
  return {
    startDate: filters.startDate || undefined,
    endDate: filters.endDate || undefined,
    category: filters.category || undefined,
    keyword: filters.keyword || undefined,
    limit: filters.limit,
    offset: filters.offset,
  };
}

export function getExpensePaginationState(
  response: Pick<ExpenseListResponse, "total" | "limit" | "offset">
) {
  const totalPages = Math.ceil(response.total / response.limit);
  const currentPage = Math.floor(response.offset / response.limit) + 1;
  return {
    totalPages,
    currentPage,
    canGoPrevious: response.offset > 0,
    canGoNext: response.offset + response.limit < response.total,
  };
}

export function getUploadFailureMessage(error: unknown, fallback: string) {
  return error instanceof ApiError ? error.message || fallback : fallback;
}

export function generateMonthlyAdvice(data: MonthlySummary): string[] {
  const advice: string[] = [];
  if (data.count === 0) {
    return ["本月暂无消费记录。先记录几笔日常开销，系统会根据数据分析消费结构。"];
  }

  const sortedByAmount = [...data.items].sort((a, b) => b.total_amount - a.total_amount);
  const top = sortedByAmount[0];
  if (top) {
    advice.push(`本月消费主要集中在「${top.category}」，可以先检查这类支出是否符合预期。`);
  }

  for (const item of data.items) {
    addCategoryAdvice(advice, item, data.total_amount);
  }

  if (data.average_daily_amount > 100) {
    advice.push(`本月日均消费为 ${data.average_daily_amount} 元，可以设置每日预算上限。`);
  }
  if (advice.length === 0) {
    advice.push("本月消费结构整体较均衡，可以继续保持记录习惯。");
  }
  return advice.slice(0, 4);
}

function addCategoryAdvice(advice: string[], item: CategoryItem, totalAmount: number) {
  const pct = totalAmount > 0 ? (item.total_amount / totalAmount) * 100 : 0;
  if (item.category === "餐饮" && pct > 50) {
    advice.push("餐饮占比较高，可以关注外卖、零食和聚餐频次。");
  }
  if (item.category === "交通" && pct > 20) {
    advice.push("交通支出占比较高，可以比较公交、地铁、步行或骑行等替代方式。");
  }
  if (item.category === "购物" && pct > 30) {
    advice.push("购物支出占比较高，购买前可以先判断是否为必要消费。");
  }
}
