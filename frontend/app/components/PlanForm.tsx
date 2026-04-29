"use client";

import { useEffect, useState } from "react";

import { usePreset } from "../hooks/usePreset";
import { apiClient, ApiError } from "../lib/api-client";
import { AdjustResult, PlanResult, SavingPlanCurrentResponse } from "../types";

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof ApiError ? error.message || fallback : fallback;
}

export function PlanForm() {
  const { preset, setField, savePreset, clearPreset, message } = usePreset();
  const [targetAmount, setTargetAmount] = useState("");
  const [deadline, setDeadline] = useState("");
  const [result, setResult] = useState<PlanResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [savedAmount, setSavedAmount] = useState("");
  const [currentPlan, setCurrentPlan] = useState<SavingPlanCurrentResponse | null>(null);

  useEffect(() => {
    void apiClient.getCurrentPlan().then(setCurrentPlan).catch(() => {});
  }, []);
  const [actualExpenseToday, setActualExpenseToday] = useState("");
  const [adjustResult, setAdjustResult] = useState<AdjustResult | null>(null);
  const [adjustError, setAdjustError] = useState("");
  const [adjustLoading, setAdjustLoading] = useState(false);

  async function generatePlan() {
    setError("");
    setResult(null);
    const income = Number(preset.monthlyIncome);
    const fixed = Number(preset.fixedExpenses);
    const target = Number(targetAmount);
    const minimum = Number(preset.minimumLivingCost);

    if (!income || income <= 0) {
      setError("月收入必须大于 0");
      return;
    }
    if (fixed < 0 || minimum < 0) {
      setError("固定支出和最低生活费不能小于 0");
      return;
    }
    if (!target || target <= 0) {
      setError("攒钱目标必须大于 0");
      return;
    }
    if (!deadline) {
      setError("请选择截止日期");
      return;
    }

    setLoading(true);
    try {
      const data = await apiClient.generatePlan({
        monthly_income: income,
        fixed_expenses: fixed,
        target_amount: target,
        deadline,
        minimum_living_cost: minimum,
        identity: preset.identity,
      });
      setResult(data);
    } catch (err) {
      setError(getErrorMessage(err, "生成失败，请确认后端已启动"));
    } finally {
      setLoading(false);
    }
  }

  async function adjustPlan() {
    setAdjustError("");
    setAdjustResult(null);
    if (!result) {
      setAdjustError("请先生成攒钱计划");
      return;
    }

    const saved = Number(savedAmount);
    const todayExpense = Number(actualExpenseToday);
    if (Number.isNaN(saved) || saved < 0 || Number.isNaN(todayExpense) || todayExpense < 0) {
      setAdjustError("已攒金额和今日消费必须是大于等于 0 的数字");
      return;
    }

    setAdjustLoading(true);
    try {
      const data = await apiClient.adjustPlan({
        target_amount: result.target_amount,
        saved_amount: saved,
        remaining_days: result.remaining_days,
        planned_daily_saving: result.daily_saving,
        actual_expense_today: todayExpense,
        daily_available: result.daily_available,
      });
      setAdjustResult(data);
    } catch (err) {
      setAdjustError(getErrorMessage(err, "调整失败，请确认后端已启动"));
    } finally {
      setAdjustLoading(false);
    }
  }

  return (
    <section className="rounded-lg border border-gray-800 p-4 sm:p-5">
      <h2 className="text-xl font-bold">攒钱计划</h2>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <label className="grid gap-1 text-sm font-medium">
          月收入
          <input
            type="number"
            value={preset.monthlyIncome}
            onChange={(event) => setField("monthlyIncome", event.target.value)}
            className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3 text-base"
            placeholder="例如 3000"
          />
        </label>
        <label className="grid gap-1 text-sm font-medium">
          固定支出
          <input
            type="number"
            value={preset.fixedExpenses}
            onChange={(event) => setField("fixedExpenses", event.target.value)}
            className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3 text-base"
            placeholder="例如 1800"
          />
        </label>
        <label className="grid gap-1 text-sm font-medium">
          攒钱目标
          <input
            type="number"
            value={targetAmount}
            onChange={(event) => setTargetAmount(event.target.value)}
            className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3 text-base"
            placeholder="例如 5000"
          />
        </label>
        <label className="grid gap-1 text-sm font-medium">
          截止日期
          <input
            type="date"
            value={deadline}
            onChange={(event) => setDeadline(event.target.value)}
            className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3 text-base"
          />
        </label>
        <label className="grid gap-1 text-sm font-medium">
          每月最低生活费
          <input
            type="number"
            value={preset.minimumLivingCost}
            onChange={(event) => setField("minimumLivingCost", event.target.value)}
            className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3 text-base"
            placeholder="例如 800"
          />
        </label>
        <label className="grid gap-1 text-sm font-medium">
          身份
          <select
            value={preset.identity}
            onChange={(event) => setField("identity", event.target.value)}
            className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3 text-base"
          >
            <option value="student">学生</option>
            <option value="worker">上班族</option>
            <option value="freelancer">自由职业者</option>
            <option value="other">其他</option>
          </select>
        </label>
      </div>

      <div className="mt-4 grid gap-2 sm:grid-cols-3">
        <button
          type="button"
          onClick={generatePlan}
          disabled={loading}
          className="min-h-12 rounded-lg bg-white px-4 font-semibold text-black disabled:opacity-60"
        >
          {loading ? "生成中..." : "生成计划"}
        </button>
        <button
          type="button"
          onClick={savePreset}
          className="min-h-12 rounded-lg border border-gray-600 px-4 font-medium"
        >
          保存常用信息
        </button>
        <button
          type="button"
          onClick={clearPreset}
          className="min-h-12 rounded-lg border border-gray-600 px-4 font-medium"
        >
          清除常用信息
        </button>
      </div>

      {message && <p className="mt-3 rounded-lg bg-gray-900 px-3 py-2 text-sm">{message}</p>}
      {error && <p className="mt-3 rounded-lg bg-red-950 px-3 py-2 text-sm">{error}</p>}

      {currentPlan?.plan && (
        <div className="mt-4 rounded-lg border border-emerald-700 bg-emerald-950 p-4 text-sm">
          <h3 className="mb-2 font-semibold text-emerald-300">🎯 当前活动计划</h3>
          <div className="grid gap-2 sm:grid-cols-2">
            <p>目标：¥{currentPlan.plan.target_amount.toLocaleString()}</p>
            <p>已攒：¥{currentPlan.plan.saved_amount.toLocaleString()}</p>
            <p>截止：{currentPlan.plan.deadline}</p>
            <p>剩余：{currentPlan.remaining_days ?? 0} 天</p>
            {currentPlan.daily_saving !== null && (
              <p>今日建议最多花：<span className="font-semibold text-yellow-300">¥{currentPlan.daily_available}</span></p>
            )}
          </div>
          {/* Progress bar */}
          <div className="mt-3 h-3 w-full rounded-full bg-gray-800">
            <div
              className="h-3 rounded-full bg-emerald-500 transition-all"
              style={{
                width: `${Math.min(
                  100,
                  Math.round((currentPlan.plan.saved_amount / currentPlan.plan.target_amount) * 100)
                )}%`,
              }}
            />
          </div>
          <p className="mt-1 text-right text-xs text-gray-400">
            {Math.round((currentPlan.plan.saved_amount / currentPlan.plan.target_amount) * 100)}% 已完成
          </p>
        </div>
      )}

      {result && (
        <div className="mt-4 grid gap-3 rounded-lg border border-gray-800 bg-gray-950 p-4 text-sm sm:grid-cols-2">
          <p>剩余天数：{result.remaining_days}</p>
          <p>每日需存：{result.daily_saving} 元</p>
          <p>每月可支配：{result.monthly_available} 元</p>
          <p>日均可支配：{result.daily_available} 元</p>
          <p>可行性评分：{result.feasibility_score} / 100</p>
          <p>状态：{result.status}</p>
          <p className="sm:col-span-2">说明：{result.message}</p>
        </div>
      )}

      <div className="mt-6 border-t border-gray-800 pt-4">
        <h3 className="font-semibold">动态调整计划</h3>
        <div className="mt-3 grid gap-3 sm:grid-cols-3">
          <input
            type="number"
            value={savedAmount}
            onChange={(event) => setSavedAmount(event.target.value)}
            className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3"
            placeholder="已攒金额"
          />
          <input
            type="number"
            value={actualExpenseToday}
            onChange={(event) => setActualExpenseToday(event.target.value)}
            className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3"
            placeholder="今日实际消费"
          />
          <button
            type="button"
            onClick={adjustPlan}
            disabled={adjustLoading}
            className="min-h-12 rounded-lg border border-gray-600 px-4 font-medium disabled:opacity-60"
          >
            {adjustLoading ? "调整中..." : "调整计划"}
          </button>
        </div>
        {adjustError && <p className="mt-3 rounded-lg bg-red-950 px-3 py-2 text-sm">{adjustError}</p>}
        {adjustResult && (
          <div className="mt-3 grid gap-2 rounded-lg bg-gray-950 p-4 text-sm sm:grid-cols-2">
            <p>剩余需攒金额：{adjustResult.remaining_amount} 元</p>
            <p>今日差距：{adjustResult.today_gap} 元</p>
            <p>新的每日需存：{adjustResult.new_daily_saving} 元</p>
            <p>每日调整幅度：{adjustResult.adjustment_per_day} 元</p>
            <p className="sm:col-span-2">建议：{adjustResult.message}</p>
          </div>
        )}
      </div>
    </section>
  );
}
