"use client";

import { useState } from "react";

type PlanResult = {
  remaining_days: number;
  daily_saving: number;
  monthly_available: number;
  daily_available: number;
  target_amount: number;
  feasibility_score: number;
  minimum_living_cost: number;
  safe_saving_capacity: number;
  status: string;
  message: string;
};

export default function Home() {
  const [monthlyIncome, setMonthlyIncome] = useState("");
  const [fixedExpenses, setFixedExpenses] = useState("");
  const [targetAmount, setTargetAmount] = useState("");
  const [deadline, setDeadline] = useState("");
  const [minimumLivingCost, setMinimumLivingCost] = useState("");
  const [identity, setIdentity] = useState("student");
  const [result, setResult] = useState<PlanResult | null>(null);
  const [error, setError] = useState("");

  async function generatePlan() {
    setError("");
    setResult(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/plans/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          monthly_income: Number(monthlyIncome),
          fixed_expenses: Number(fixedExpenses),
          target_amount: Number(targetAmount),
          deadline,
          minimum_living_cost: Number(minimumLivingCost),
          identity,
        }),
      });

      if (!response.ok) {
        throw new Error("请求失败");
      }

      const data: PlanResult = await response.json();
      setResult(data);
    } catch {
      setError("生成失败，请确认后端已启动");
    }
  }

  return (
    <main className="min-h-screen p-8">
      <h1 className="text-3xl font-bold">SaveMoney AI</h1>

      <p className="mt-4 text-gray-600">
        AI 攒钱计划助手：根据收入、支出和目标生成每日存钱计划。
      </p>

      <section className="mt-6 flex max-w-md flex-col gap-4">
        <label className="flex flex-col gap-1 text-sm font-medium">
          月收入
          <input
            type="number"
            value={monthlyIncome}
            onChange={(e) => setMonthlyIncome(e.target.value)}
            className="rounded-lg border px-3 py-2"
            placeholder="例如 3000"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm font-medium">
          固定支出
          <input
            type="number"
            value={fixedExpenses}
            onChange={(e) => setFixedExpenses(e.target.value)}
            className="rounded-lg border px-3 py-2"
            placeholder="例如 1800"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm font-medium">
          攒钱目标
          <input
            type="number"
            value={targetAmount}
            onChange={(e) => setTargetAmount(e.target.value)}
            className="rounded-lg border px-3 py-2"
            placeholder="例如 5000"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm font-medium">
          截止日期
          <input
            type="date"
            value={deadline}
            onChange={(e) => setDeadline(e.target.value)}
            className="rounded-lg border px-3 py-2"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm font-medium">
          每月最低生活费
          <input
            type="number"
            value={minimumLivingCost}
            onChange={(e) => setMinimumLivingCost(e.target.value)}
            className="rounded-lg border px-3 py-2"
            placeholder="例如 800"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm font-medium">
          身份
          <select
            value={identity}
            onChange={(e) => setIdentity(e.target.value)}
            className="rounded-lg border border-gray-600 px-3 py-2 bg-gray-900 text-white"
          >
            <option value="student">学生</option>
            <option value="worker">上班族</option>
            <option value="freelancer">自由职业者</option>
            <option value="other">其他</option>
          </select>
        </label>

        <button
          onClick={generatePlan}
          className="mt-2 rounded-lg bg-black px-4 py-2 text-white"
        >
          生成攒钱计划
        </button>
      </section>

      {error && (
        <p className="mt-6 text-red-600 font-medium">{error}</p>
      )}

      {result && (
        <section className="mt-6 rounded-xl border p-4 max-w-md">
          <p>剩余天数：{result.remaining_days}</p>
          <p>每日需存：{result.daily_saving} 元</p>
          <p>每月可支配：{result.monthly_available} 元</p>
          <p>攒钱目标：{result.target_amount} 元</p>
          <p>日均可支配：{result.daily_available} 元</p>
          <p>可行性评分：{result.feasibility_score} / 100</p>
          <p>每月最低生活费：{result.minimum_living_cost} 元</p>
          <p>安全可攒金额：{result.safe_saving_capacity} 元</p>
          <p>状态：{result.status}</p>
          <p>说明：{result.message}</p>
        </section>
      )}
    </main>
  );
}