"use client";

import { useState } from "react";

import { apiClient, ApiError } from "../lib/api-client";

function getTodayLocalDateString() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getCurrentMonthStartDateString() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}-01`;
}

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof ApiError ? error.message || fallback : fallback;
}

export function ExportPanel() {
  const [startDate, setStartDate] = useState(getCurrentMonthStartDateString());
  const [endDate, setEndDate] = useState(getTodayLocalDateString());
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function doExport(start: string, end: string) {
    setError("");
    setMessage("");
    setStartDate(start);
    setEndDate(end);

    if (!start || !end) {
      setError("请选择开始日期和结束日期");
      return;
    }
    if (start > end) {
      setError("开始日期不能晚于结束日期");
      return;
    }

    setLoading(true);
    try {
      const blob = await apiClient.exportExpensesCsv(start, end);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `expenses_${start}_to_${end}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      setMessage("CSV 已导出");
    } catch (err) {
      setError(getErrorMessage(err, "导出失败，请确认后端已启动"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-lg border border-gray-800 p-4 sm:p-5">
      <h2 className="text-xl font-bold">导出消费记录</h2>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <label className="grid gap-1 text-sm font-medium">
          开始日期
          <input
            type="date"
            value={startDate}
            onChange={(event) => setStartDate(event.target.value)}
            className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3"
          />
        </label>
        <label className="grid gap-1 text-sm font-medium">
          结束日期
          <input
            type="date"
            value={endDate}
            onChange={(event) => setEndDate(event.target.value)}
            className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3"
          />
        </label>
      </div>
      <div className="mt-4 grid gap-2 sm:grid-cols-3">
        <button
          type="button"
          onClick={() => void doExport(startDate, endDate)}
          disabled={loading}
          className="min-h-12 rounded-lg bg-white px-4 font-semibold text-black disabled:opacity-60"
        >
          {loading ? "导出中..." : "导出 CSV"}
        </button>
        <button
          type="button"
          onClick={() => void doExport(getTodayLocalDateString(), getTodayLocalDateString())}
          className="min-h-12 rounded-lg border border-gray-600 px-4 font-medium"
        >
          导出今日
        </button>
        <button
          type="button"
          onClick={() => void doExport(getCurrentMonthStartDateString(), getTodayLocalDateString())}
          className="min-h-12 rounded-lg border border-gray-600 px-4 font-medium"
        >
          导出本月
        </button>
      </div>
      {message && <p className="mt-3 rounded-lg bg-emerald-950 px-3 py-2 text-sm">{message}</p>}
      {error && <p className="mt-3 rounded-lg bg-red-950 px-3 py-2 text-sm">{error}</p>}
    </section>
  );
}
