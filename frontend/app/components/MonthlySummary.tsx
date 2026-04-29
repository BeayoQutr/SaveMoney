"use client";

import { useCallback, useEffect, useState } from "react";

import { apiClient, ApiError } from "../lib/api-client";
import { CategoryItem, DailySummary, MonthlySummary as MonthlySummaryType } from "../types";

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

function getCurrentMonthKey() {
  return getCurrentMonthStartDateString().substring(0, 7);
}

function getErrorMessage(error: unknown, fallback: string) {
  if (error instanceof ApiError) {
    if (error.status === 502) {
      return "AI 服务暂时不可用，请稍后再试";
    }
    return error.message || fallback;
  }
  return fallback;
}

function generateMonthlyAdvice(data: MonthlySummaryType): string[] {
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
    const pct = data.total_amount > 0 ? (item.total_amount / data.total_amount) * 100 : 0;
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

  if (data.average_daily_amount > 100) {
    advice.push(`本月日均消费为 ${data.average_daily_amount} 元，可以设置每日预算上限。`);
  }
  if (advice.length === 0) {
    advice.push("本月消费结构整体较均衡，可以继续保持记录习惯。");
  }
  return advice.slice(0, 4);
}

type MonthlySummaryProps = {
  refreshKey: number;
};

export function MonthlySummary({ refreshKey }: MonthlySummaryProps) {
  const [monthly, setMonthly] = useState<MonthlySummaryType | null>(null);
  const [monthlyAdvice, setMonthlyAdvice] = useState<string[]>([]);
  const [monthlyError, setMonthlyError] = useState("");
  const [monthlyLoading, setMonthlyLoading] = useState(false);
  const [aiAdvice, setAiAdvice] = useState("");
  const [aiError, setAiError] = useState("");
  const [aiLoading, setAiLoading] = useState(false);

  const [summaryDate, setSummaryDate] = useState(getTodayLocalDateString());
  const [dailySummary, setDailySummary] = useState<DailySummary | null>(null);
  const [dailyError, setDailyError] = useState("");
  const [dailyLoading, setDailyLoading] = useState(false);

  const [categoryStartDate, setCategoryStartDate] = useState(getCurrentMonthStartDateString());
  const [categoryEndDate, setCategoryEndDate] = useState(getTodayLocalDateString());
  const [categoryItems, setCategoryItems] = useState<CategoryItem[] | null>(null);
  const [categoryError, setCategoryError] = useState("");
  const [categoryLoading, setCategoryLoading] = useState(false);

  const fetchMonthlySummary = useCallback(async () => {
    setMonthlyLoading(true);
    setMonthlyError("");
    try {
      const data = await apiClient.monthlySummary(getCurrentMonthKey());
      setMonthly(data);
      setMonthlyAdvice(generateMonthlyAdvice(data));
    } catch (err) {
      setMonthlyError(getErrorMessage(err, "本月总览查询失败，请确认后端已启动"));
      setMonthlyAdvice([]);
    } finally {
      setMonthlyLoading(false);
    }
  }, []);

  useEffect(() => {
    void Promise.resolve().then(fetchMonthlySummary);
  }, [fetchMonthlySummary, refreshKey]);

  async function fetchDailySummary() {
    setDailyLoading(true);
    setDailyError("");
    setDailySummary(null);
    if (!summaryDate) {
      setDailyError("请选择查询日期");
      setDailyLoading(false);
      return;
    }
    try {
      setDailySummary(await apiClient.dailySummary(summaryDate));
    } catch (err) {
      setDailyError(getErrorMessage(err, "每日消费汇总查询失败，请确认后端已启动"));
    } finally {
      setDailyLoading(false);
    }
  }

  async function fetchCategorySummary(start: string, end: string) {
    setCategoryLoading(true);
    setCategoryError("");
    setCategoryItems(null);
    setCategoryStartDate(start);
    setCategoryEndDate(end);
    if (!start || !end) {
      setCategoryError("请选择开始日期和结束日期");
      setCategoryLoading(false);
      return;
    }
    if (start > end) {
      setCategoryError("开始日期不能晚于结束日期");
      setCategoryLoading(false);
      return;
    }
    try {
      const data = await apiClient.categorySummary(start, end);
      setCategoryItems(data.items);
    } catch (err) {
      setCategoryError(getErrorMessage(err, "消费分类统计查询失败，请确认后端已启动"));
    } finally {
      setCategoryLoading(false);
    }
  }

  async function fetchAiAdvice() {
    setAiLoading(true);
    setAiError("");
    setAiAdvice("");
    try {
      const data = await apiClient.aiMonthlyAdvice(getCurrentMonthKey());
      setAiAdvice(data.advice);
    } catch (err) {
      setAiError(getErrorMessage(err, "AI 消费分析生成失败，请稍后重试"));
    } finally {
      setAiLoading(false);
    }
  }

  return (
    <section className="min-w-0 rounded-lg border border-gray-800 p-4 sm:p-5">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-xl font-bold">本月总览与统计</h2>
        <button
          type="button"
          onClick={() => void fetchMonthlySummary()}
          className="min-h-11 rounded-lg border border-gray-600 px-4 font-medium"
        >
          {monthlyLoading ? "刷新中..." : "刷新总览"}
        </button>
      </div>

      {monthlyError && <p className="mt-3 rounded-lg bg-red-950 px-3 py-2 text-sm">{monthlyError}</p>}
      {monthlyLoading && !monthly && (
        <p className="mt-3 rounded-lg bg-gray-950 px-3 py-3 text-sm text-gray-300">
          正在加载本月总览...
        </p>
      )}
      {monthly && (
        <div className="mt-4 grid gap-3 rounded-lg bg-gray-950 p-4 text-sm sm:grid-cols-2">
          <p>当前月份：{monthly.month}</p>
          <p>本月总消费：{monthly.total_amount} 元</p>
          <p>本月消费笔数：{monthly.count}</p>
          <p>日均消费：{monthly.average_daily_amount} 元</p>
        </div>
      )}

      {monthlyAdvice.length > 0 && (
        <div className="mt-4 grid gap-2">
          <h3 className="font-semibold">本月消费建议</h3>
          {monthlyAdvice.map((line) => (
            <p key={line} className="rounded-lg border border-gray-800 bg-gray-950 px-3 py-2 text-sm">
              {line}
            </p>
          ))}
        </div>
      )}

      {monthly?.items && monthly.items.length > 0 && (
        <div className="mt-4 grid gap-2">
          <h3 className="font-semibold">本月分类明细</h3>
          {monthly.items.map((item) => (
            <p key={item.category} className="rounded-lg bg-gray-950 px-3 py-2 text-sm">
              {item.category}：{item.total_amount} 元，{item.count} 笔
            </p>
          ))}
        </div>
      )}
      {monthly && monthly.items.length === 0 && !monthlyError && (
        <p className="mt-4 rounded-lg border border-gray-800 bg-gray-950 px-3 py-3 text-sm text-gray-300">
          本月还没有分类明细。记录消费后会显示各分类的金额和笔数。
        </p>
      )}

      <div className="mt-5 grid gap-2">
        <button
          type="button"
          onClick={() => void fetchAiAdvice()}
          disabled={aiLoading}
          className="min-h-12 rounded-lg border border-gray-600 px-4 font-medium disabled:opacity-60"
        >
          {aiLoading ? "AI 建议生成中..." : "生成 AI 消费分析"}
        </button>
        {aiError && <p className="rounded-lg bg-red-950 px-3 py-2 text-sm">{aiError}</p>}
        {aiAdvice && (
          <p className="whitespace-pre-line rounded-lg bg-gray-950 px-3 py-3 text-sm">{aiAdvice}</p>
        )}
      </div>

      <div className="mt-6 grid gap-4 border-t border-gray-800 pt-4 lg:grid-cols-2">
        <div>
          <h3 className="font-semibold">每日消费汇总</h3>
          <div className="mt-3 grid gap-2 sm:grid-cols-[1fr_auto]">
            <input
              type="date"
              value={summaryDate}
              onChange={(event) => setSummaryDate(event.target.value)}
              className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3"
            />
            <button
              type="button"
              onClick={() => void fetchDailySummary()}
              className="min-h-12 rounded-lg border border-gray-600 px-4 font-medium"
            >
              {dailyLoading ? "查询中..." : "查询"}
            </button>
          </div>
          {dailyError && <p className="mt-3 rounded-lg bg-red-950 px-3 py-2 text-sm">{dailyError}</p>}
          {dailySummary && (
            <p className="mt-3 rounded-lg bg-gray-950 px-3 py-3 text-sm">
              {dailySummary.date} 共消费 {dailySummary.total_amount} 元，{dailySummary.count} 笔
            </p>
          )}
        </div>

        <div>
          <h3 className="font-semibold">消费分类统计</h3>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            <input
              type="date"
              value={categoryStartDate}
              onChange={(event) => setCategoryStartDate(event.target.value)}
              className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3"
            />
            <input
              type="date"
              value={categoryEndDate}
              onChange={(event) => setCategoryEndDate(event.target.value)}
              className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3"
            />
          </div>
          <div className="mt-2 grid gap-2 sm:grid-cols-3">
            <button
              type="button"
              onClick={() => void fetchCategorySummary(categoryStartDate, categoryEndDate)}
              className="min-h-11 rounded-lg border border-gray-600 px-3 text-sm font-medium"
            >
              {categoryLoading ? "查询中..." : "查询范围"}
            </button>
            <button
              type="button"
              onClick={() =>
                void fetchCategorySummary(getTodayLocalDateString(), getTodayLocalDateString())
              }
              className="min-h-11 rounded-lg border border-gray-600 px-3 text-sm font-medium"
            >
              查询今日
            </button>
            <button
              type="button"
              onClick={() =>
                void fetchCategorySummary(getCurrentMonthStartDateString(), getTodayLocalDateString())
              }
              className="min-h-11 rounded-lg border border-gray-600 px-3 text-sm font-medium"
            >
              查询本月
            </button>
          </div>
          {categoryError && (
            <p className="mt-3 rounded-lg bg-red-950 px-3 py-2 text-sm">{categoryError}</p>
          )}
          {categoryItems && categoryItems.length === 0 && (
            <p className="mt-3 rounded-lg bg-gray-950 px-3 py-3 text-sm">该日期范围内暂无消费记录</p>
          )}
          {categoryItems && categoryItems.length > 0 && (
            <div className="mt-3 grid gap-2">
              {categoryItems.map((item) => (
                <p key={item.category} className="rounded-lg bg-gray-950 px-3 py-2 text-sm">
                  {item.category}：{item.total_amount} 元，{item.count} 笔
                </p>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
