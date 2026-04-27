"use client";

import { useState, useEffect, useCallback } from "react";

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

type ExpenseResult = {
  amount: number;
  note: string;
  date: string;
  category: string;
  message: string;
};

type ExpenseItem = {
  id: number;
  amount: number;
  note: string;
  date: string;
  category: string;
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

  const [expenseAmount, setExpenseAmount] = useState("");
  const [expenseNote, setExpenseNote] = useState("");
  const [expenseDate, setExpenseDate] = useState("");
  const [expenseResult, setExpenseResult] = useState<ExpenseResult | null>(null);
  const [expenseError, setExpenseError] = useState("");
  const [expenseList, setExpenseList] = useState<ExpenseItem[]>([]);
  const [expenseListError, setExpenseListError] = useState("");

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

  const fetchExpenses = useCallback(async () => {
    setExpenseListError("");
    try {
      const response = await fetch("http://127.0.0.1:8000/expenses");
      if (!response.ok) {
        throw new Error("请求失败");
      }
      const data: ExpenseItem[] = await response.json();
      setExpenseList(data);
    } catch {
      setExpenseListError("消费记录加载失败，请确认后端已启动");
    }
  }, []);

  useEffect(() => {
    /* eslint-disable */
    void fetchExpenses();
    /* eslint-enable */
  }, []);

  async function recordExpense() {
    setExpenseError("");
    setExpenseResult(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/expenses", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          amount: Number(expenseAmount),
          note: expenseNote,
          date: expenseDate,
        }),
      });

      if (!response.ok) {
        throw new Error("请求失败");
      }

      const data: ExpenseResult = await response.json();
      setExpenseResult(data);
      fetchExpenses();
    } catch {
      setExpenseError("记录失败，请确认后端已启动");
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

      <hr className="mt-8 max-w-md border-gray-700" />

      <h2 className="mt-8 text-2xl font-bold">记录今日消费</h2>

      <section className="mt-4 flex max-w-md flex-col gap-4">
        <label className="flex flex-col gap-1 text-sm font-medium">
          消费金额
          <input
            type="number"
            value={expenseAmount}
            onChange={(e) => setExpenseAmount(e.target.value)}
            className="rounded-lg border px-3 py-2"
            placeholder="例如 35"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm font-medium">
          消费备注
          <input
            type="text"
            value={expenseNote}
            onChange={(e) => setExpenseNote(e.target.value)}
            className="rounded-lg border px-3 py-2"
            placeholder="例如 午餐"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm font-medium">
          消费日期
          <input
            type="date"
            value={expenseDate}
            onChange={(e) => setExpenseDate(e.target.value)}
            className="rounded-lg border px-3 py-2"
          />
        </label>

        <button
          onClick={recordExpense}
          className="mt-2 rounded-lg bg-black px-4 py-2 text-white"
        >
          记录消费
        </button>
      </section>

      {expenseError && (
        <p className="mt-4 text-red-600 font-medium">{expenseError}</p>
      )}

      {expenseResult && (
        <section className="mt-4 rounded-xl border p-4 max-w-md">
          <p>消费金额：{expenseResult.amount} 元</p>
          <p>备注：{expenseResult.note}</p>
          <p>日期：{expenseResult.date}</p>
          <p>分类：{expenseResult.category}</p>
          <p>说明：{expenseResult.message}</p>
        </section>
      )}

      <hr className="mt-8 max-w-md border-gray-700" />

      <h2 className="mt-8 text-2xl font-bold">最近消费记录</h2>

      {expenseListError && (
        <p className="mt-4 text-red-600 font-medium">{expenseListError}</p>
      )}

      {expenseList.length > 0 && (
        <section className="mt-4 max-w-md flex flex-col gap-3">
          {expenseList.map((item) => (
            <div
              key={item.id}
              className="rounded-xl border border-gray-700 p-3"
            >
              <p>
                <span className="text-gray-400">金额：</span>
                {item.amount} 元
              </p>
              <p>
                <span className="text-gray-400">备注：</span>
                {item.note}
              </p>
              <p>
                <span className="text-gray-400">日期：</span>
                {item.date}
              </p>
              <p>
                <span className="text-gray-400">分类：</span>
                {item.category}
              </p>
            </div>
          ))}
        </section>
      )}
    </main>
  );
}