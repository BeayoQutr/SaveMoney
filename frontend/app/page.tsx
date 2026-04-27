"use client";

import { useState } from "react";

type PlanResult = {
  remaining_days: number;
  daily_saving: number;
  monthly_available: number;
  status: string;
  message: string;
};

export default function Home() {
  const [result, setResult] = useState<PlanResult | null>(null);

  async function generatePlan() {
    const response = await fetch("http://127.0.0.1:8000/plans/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        monthly_income: 3000,
        fixed_expenses: 1800,
        target_amount: 5000,
        deadline: "2026-06-30",
      }),
    });

    const data = await response.json();
    setResult(data);
  }

  return (
    <main className="min-h-screen p-8">
      <h1 className="text-3xl font-bold">SaveMoney AI</h1>

      <p className="mt-4 text-gray-600">
        AI 攒钱计划助手：根据收入、支出和目标生成每日存钱计划。
      </p>

      <button
        onClick={generatePlan}
        className="mt-6 rounded-lg bg-black px-4 py-2 text-white"
      >
        生成测试攒钱计划
      </button>

      {result && (
        <section className="mt-6 rounded-xl border p-4">
          <p>剩余天数：{result.remaining_days}</p>
          <p>每日需存：{result.daily_saving} 元</p>
          <p>每月可支配：{result.monthly_available} 元</p>
          <p>状态：{result.status}</p>
          <p>说明：{result.message}</p>
        </section>
      )}
    </main>
  );
}