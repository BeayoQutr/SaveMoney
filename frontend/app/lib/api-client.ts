import {
  AdjustPlanPayload,
  AdjustResult,
  AiMonthlyAdviceResponse,
  AiOptimizeNoteResponse,
  AiSuggestCategoryResponse,
  CategorySummary,
  DailySummary,
  ExpenseItem,
  ExpensePayload,
  ExpenseResult,
  GeneratePlanPayload,
  MonthlySummary,
  PlanResult,
} from "../types";
import { API_BASE_URL } from "./api";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function readError(response: Response, fallback: string) {
  try {
    const data: unknown = await response.json();
    if (
      typeof data === "object" &&
      data !== null &&
      "detail" in data &&
      typeof data.detail === "string"
    ) {
      return data.detail;
    }
  } catch {
    return fallback;
  }
  return fallback;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    throw new ApiError(await readError(response, "请求失败"), response.status);
  }
  return response.json() as Promise<T>;
}

export const apiClient = {
  health() {
    return requestJson<{ status: string }>("/health");
  },
  generatePlan(payload: GeneratePlanPayload) {
    return requestJson<PlanResult>("/plans/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },
  adjustPlan(payload: AdjustPlanPayload) {
    return requestJson<AdjustResult>("/plans/adjust", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },
  listExpenses() {
    return requestJson<ExpenseItem[]>("/expenses");
  },
  createExpense(payload: ExpensePayload) {
    return requestJson<ExpenseResult>("/expenses", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },
  updateExpense(id: number, payload: ExpensePayload) {
    return requestJson<ExpenseResult>(`/expenses/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },
  deleteExpense(id: number) {
    return requestJson<{ message: string; deleted_id: number }>(`/expenses/${id}`, {
      method: "DELETE",
    });
  },
  dailySummary(date: string) {
    return requestJson<DailySummary>(`/expenses/summary/daily?query_date=${date}`);
  },
  categorySummary(startDate: string, endDate: string) {
    return requestJson<CategorySummary>(
      `/expenses/summary/category?start_date=${startDate}&end_date=${endDate}`
    );
  },
  monthlySummary(month: string) {
    return requestJson<MonthlySummary>(`/expenses/summary/monthly?month=${month}`);
  },
  aiMonthlyAdvice(month: string) {
    return requestJson<AiMonthlyAdviceResponse>(`/ai/monthly-advice?month=${month}`);
  },
  suggestCategory(amount: number, note: string) {
    return requestJson<AiSuggestCategoryResponse>("/ai/suggest-category", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount, note }),
    });
  },
  optimizeNote(note: string) {
    return requestJson<AiOptimizeNoteResponse>("/ai/optimize-note", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ note }),
    });
  },
  async exportExpensesCsv(startDate: string, endDate: string) {
    const response = await fetch(
      `${API_BASE_URL}/expenses/export/csv?start_date=${startDate}&end_date=${endDate}`
    );
    if (!response.ok) {
      throw new ApiError(await readError(response, "导出失败"), response.status);
    }
    return response.blob();
  },
};
