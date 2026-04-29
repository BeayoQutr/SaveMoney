import {
  AdjustPlanPayload,
  AdjustResult,
  AiMonthlyAdviceResponse,
  AiOptimizeNoteResponse,
  AiSuggestCategoryResponse,
  CategorySummary,
  DailySummary,
  ExpenseListResponse,
  ExpensePayload,
  ExpenseResult,
  GeneratePlanPayload,
  MonthlySummary,
  PlanResult,
  SavingPlanCurrentResponse,
} from "../types";
import { API_BASE_URL } from "./api";

function getAuthHeaders(): Record<string, string> {
  const token = process.env.NEXT_PUBLIC_SAVEMONEY_ACCESS_TOKEN;
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

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
  const authHeaders = getAuthHeaders();
  const mergedInit: RequestInit = {
    ...init,
    headers: {
      ...authHeaders,
      ...(init?.headers as Record<string, string>),
    },
  };
  const response = await fetch(`${API_BASE_URL}${path}`, mergedInit);
  if (!response.ok) {
    throw new ApiError(await readError(response, "请求失败"), response.status);
  }
  return response.json() as Promise<T>;
}

export const apiClient = {
  health() {
    return requestJson<{ status: string }>("/health");
  },
  aiStatus() {
    return requestJson<{ ai_configured: boolean }>("/ai/status");
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
  getCurrentPlan() {
    return requestJson<SavingPlanCurrentResponse>("/plans/current");
  },
  updatePlanSavedAmount(planId: number, savedAmount: number) {
    return requestJson("/plans/" + planId, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ saved_amount: savedAmount }),
    });
  },
  listExpenses(filters?: {
    startDate?: string;
    endDate?: string;
    category?: string;
    keyword?: string;
    limit?: number;
    offset?: number;
  }) {
    const params = new URLSearchParams();
    if (filters?.startDate) params.set("start_date", filters.startDate);
    if (filters?.endDate) params.set("end_date", filters.endDate);
    if (filters?.category) params.set("category", filters.category);
    if (filters?.keyword) params.set("keyword", filters.keyword);
    if (filters?.limit !== undefined) params.set("limit", String(filters.limit));
    if (filters?.offset !== undefined) params.set("offset", String(filters.offset));
    const qs = params.toString();
    return requestJson<ExpenseListResponse>(`/expenses${qs ? `?${qs}` : ""}`);
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
    const params = new URLSearchParams({ query_date: date });
    return requestJson<DailySummary>(`/expenses/summary/daily?${params.toString()}`);
  },
  categorySummary(startDate: string, endDate: string) {
    const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
    return requestJson<CategorySummary>(
      `/expenses/summary/category?${params.toString()}`
    );
  },
  monthlySummary(month: string) {
    const params = new URLSearchParams({ month });
    return requestJson<MonthlySummary>(`/expenses/summary/monthly?${params.toString()}`);
  },
  aiMonthlyAdvice(month: string) {
    const params = new URLSearchParams({ month });
    return requestJson<AiMonthlyAdviceResponse>(`/ai/monthly-advice?${params.toString()}`);
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
  async downloadDbBackup() {
    const response = await fetch(`${API_BASE_URL}/backup/download-db`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      throw new ApiError(await readError(response, "数据库下载失败"), response.status);
    }

    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = objectUrl;
    a.download = "savemoney.db";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(objectUrl);
  },

  async restoreDb(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch(`${API_BASE_URL}/backup/restore-db`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: formData,
    });
    if (!response.ok) {
      throw new ApiError(await readError(response, "数据库恢复失败"), response.status);
    }
    return response.json() as Promise<{ message: string; backup_path: string }>;
  },

  async importCsv(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch(`${API_BASE_URL}/backup/import-csv`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: formData,
    });
    if (!response.ok) {
      throw new ApiError(await readError(response, "CSV 导入失败"), response.status);
    }
    return response.json() as Promise<{
      message: string;
      imported: number;
      errors: string[];
      backup_path: string;
    }>;
  },

  async exportExpensesCsv(startDate: string, endDate: string) {
    const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
    const response = await fetch(
      `${API_BASE_URL}/expenses/export/csv?${params.toString()}`,
      { headers: getAuthHeaders() }
    );
    if (!response.ok) {
      throw new ApiError(await readError(response, "导出失败"), response.status);
    }
    return response.blob();
  },
};
