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
import { getApiErrorMessage } from "./api-error";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

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
    const message = getApiErrorMessage(data);
    if (message) {
      return message;
    }
  } catch {
    return fallback;
  }
  return fallback;
}

const DEFAULT_TIMEOUT_MS = 10000;

async function requestJson<T>(
  path: string,
  init?: RequestInit & { signal?: AbortSignal },
  fallback = "请求失败"
): Promise<T> {
  const authHeaders = getAuthHeaders();
  const { signal: externalSignal, ...restInit } = init || {};
  const mergedInit: RequestInit = {
    ...restInit,
    signal: externalSignal ?? AbortSignal.timeout(DEFAULT_TIMEOUT_MS),
    headers: {
      ...authHeaders,
      ...(init?.headers as Record<string, string>),
    },
  };
  const response = await fetch(`${API_BASE_URL}${path}`, mergedInit);
  if (!response.ok) {
    throw new ApiError(await readError(response, fallback), response.status);
  }
  return response.json() as Promise<T>;
}

async function requestBlob(path: string, fallback: string, signal?: AbortSignal): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: getAuthHeaders(),
    signal: signal ?? AbortSignal.timeout(DEFAULT_TIMEOUT_MS),
  });
  if (!response.ok) {
    throw new ApiError(await readError(response, fallback), response.status);
  }
  return response.blob();
}

async function uploadJson<T>(
  path: string,
  fileField: string,
  file: File,
  fallback: string
): Promise<T> {
  const formData = new FormData();
  formData.append(fileField, file);
  return requestJson<T>(
    path,
    {
      method: "POST",
      body: formData,
    },
    fallback
  );
}

export const apiClient = {
  health(signal?: AbortSignal) {
    return requestJson<{ status: string }>("/health", { signal });
  },
  aiStatus(signal?: AbortSignal) {
    return requestJson<{ ai_configured: boolean }>("/ai/status", { signal });
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
  getCurrentPlan(signal?: AbortSignal) {
    return requestJson<SavingPlanCurrentResponse>("/plans/current", { signal });
  },
  updatePlanSavedAmount(planId: number, savedAmount: number) {
    return requestJson("/plans/" + planId, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ saved_amount: savedAmount }),
    });
  },
  listExpenses(
    filters?: {
      startDate?: string;
      endDate?: string;
      category?: string;
      keyword?: string;
      limit?: number;
      offset?: number;
    },
    signal?: AbortSignal
  ) {
    const params = new URLSearchParams();
    if (filters?.startDate) params.set("start_date", filters.startDate);
    if (filters?.endDate) params.set("end_date", filters.endDate);
    if (filters?.category) params.set("category", filters.category);
    if (filters?.keyword) params.set("keyword", filters.keyword);
    if (filters?.limit !== undefined) params.set("limit", String(filters.limit));
    if (filters?.offset !== undefined) params.set("offset", String(filters.offset));
    const qs = params.toString();
    return requestJson<ExpenseListResponse>(`/expenses${qs ? `?${qs}` : ""}`, { signal });
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
  monthlySummary(month: string, signal?: AbortSignal) {
    const params = new URLSearchParams({ month });
    return requestJson<MonthlySummary>(`/expenses/summary/monthly?${params.toString()}`, { signal });
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
    const blob = await requestBlob("/backup/download-db", "数据库下载失败");
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
    return uploadJson<{ message: string; backup_path: string }>(
      "/backup/restore-db",
      "file",
      file,
      "数据库恢复失败"
    );
  },

  async importCsv(file: File) {
    return uploadJson<{
      message: string;
      imported: number;
      errors: string[];
      backup_path: string;
    }>("/backup/import-csv", "file", file, "CSV 导入失败");
  },

  async exportExpensesCsv(startDate: string, endDate: string) {
    const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
    return requestBlob(`/expenses/export/csv?${params.toString()}`, "导出失败");
  },
};
