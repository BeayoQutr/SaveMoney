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

type DailySummary = {
  date: string;
  total_amount: number;
  count: number;
};

type AdjustResult = {
  remaining_amount: number;
  today_gap: number;
  new_daily_saving: number;
  adjustment_per_day: number;
  status: string;
  message: string;
};

type CategoryItem = {
  category: string;
  total_amount: number;
  count: number;
};

type MonthlySummary = {
  month: string;
  total_amount: number;
  count: number;
  average_daily_amount: number;
  items: CategoryItem[];
};

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

  const [summaryDate, setSummaryDate] = useState("");
  const [summaryResult, setSummaryResult] = useState<DailySummary | null>(null);
  const [summaryError, setSummaryError] = useState("");

  const [savedAmount, setSavedAmount] = useState("");
  const [actualExpenseToday, setActualExpenseToday] = useState("");
  const [adjustResult, setAdjustResult] = useState<AdjustResult | null>(null);
  const [adjustError, setAdjustError] = useState("");

  const [categoryStartDate, setCategoryStartDate] = useState("");
  const [categoryEndDate, setCategoryEndDate] = useState("");
  const [categoryResult, setCategoryResult] = useState<CategoryItem[] | null>(null);
  const [categoryError, setCategoryError] = useState("");

  const [monthlyResult, setMonthlyResult] = useState<MonthlySummary | null>(null);
  const [monthlyError, setMonthlyError] = useState("");

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

  async function adjustPlan() {
    setAdjustError("");
    setAdjustResult(null);

    if (!result) {
      setAdjustError("请先生成攒钱计划");
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:8000/plans/adjust", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          target_amount: result.target_amount,
          saved_amount: Number(savedAmount),
          remaining_days: result.remaining_days,
          planned_daily_saving: result.daily_saving,
          actual_expense_today: Number(actualExpenseToday),
          daily_available: result.daily_available,
        }),
      });

      if (!response.ok) {
        throw new Error("请求失败");
      }

      const data: AdjustResult = await response.json();
      setAdjustResult(data);
    } catch {
      setAdjustError("调整失败，请确认后端已启动");
    }
  }

  async function fillTodayExpense() {
    const today = getTodayLocalDateString();
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/expenses/summary/daily?query_date=${today}`
      );
      if (!response.ok) {
        throw new Error("请求失败");
      }
      const data: DailySummary = await response.json();
      setActualExpenseToday(String(data.total_amount));
    } catch {
      setAdjustError("自动读取今日消费失败");
    }
  }

  async function querySummary() {
    setSummaryError("");
    setSummaryResult(null);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/expenses/summary/daily?query_date=${summaryDate}`
      );
      if (!response.ok) {
        throw new Error("请求失败");
      }
      const data: DailySummary = await response.json();
      setSummaryResult(data);
    } catch {
      setSummaryError("消费汇总查询失败，请确认后端已启动");
    }
  }

  async function queryCategorySummaryByRange(start: string, end: string) {
    setCategoryError("");
    setCategoryResult(null);
    setCategoryStartDate(start);
    setCategoryEndDate(end);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/expenses/summary/category?start_date=${start}&end_date=${end}`
      );
      if (!response.ok) {
        throw new Error("请求失败");
      }
      const data = await response.json();
      setCategoryResult(data.items);
    } catch {
      setCategoryError("查询消费分类统计失败");
    }
  }

  async function queryCategorySummary() {
    await queryCategorySummaryByRange(categoryStartDate, categoryEndDate);
  }

  async function fetchMonthlySummary() {
    setMonthlyError("");
    setMonthlyResult(null);

    try {
      const monthKey = getCurrentMonthStartDateString().substring(0, 7);
      const response = await fetch(
        `http://127.0.0.1:8000/expenses/summary/monthly?month=${monthKey}`
      );
      if (!response.ok) {
        throw new Error("请求失败");
      }
      const data: MonthlySummary = await response.json();
      setMonthlyResult(data);
    } catch {
      setMonthlyError("本月总览查询失败，请检查后端服务");
    }
  }

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
      fetchMonthlySummary();
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

      <h2 className="mt-8 text-2xl font-bold">动态调整计划</h2>

      <section className="mt-4 flex max-w-md flex-col gap-4">
        <label className="flex flex-col gap-1 text-sm font-medium">
          已攒金额
          <input
            type="number"
            value={savedAmount}
            onChange={(e) => setSavedAmount(e.target.value)}
            className="rounded-lg border px-3 py-2"
            placeholder="例如 500"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm font-medium">
          今日实际消费
          <input
            type="number"
            value={actualExpenseToday}
            onChange={(e) => setActualExpenseToday(e.target.value)}
            className="rounded-lg border px-3 py-2"
            placeholder="例如 50"
          />
        </label>

        <button
          onClick={fillTodayExpense}
          className="rounded-lg border px-3 py-2 text-sm text-gray-400 hover:text-white"
        >
          自动填入今日消费
        </button>

        <button
          onClick={adjustPlan}
          className="mt-2 rounded-lg bg-black px-4 py-2 text-white"
        >
          调整计划
        </button>
      </section>

      {adjustError && (
        <p className="mt-4 text-red-600 font-medium">{adjustError}</p>
      )}

      {adjustResult && (
        <section className="mt-4 rounded-xl border p-4 max-w-md">
          <p>剩余需攒金额：{adjustResult.remaining_amount} 元</p>
          <p>今日差距：{adjustResult.today_gap} 元</p>
          <p>新的每日需存：{adjustResult.new_daily_saving} 元</p>
          <p>每日调整幅度：{adjustResult.adjustment_per_day} 元</p>
          <p>状态：{adjustResult.status}</p>
          <p>建议：{adjustResult.message}</p>
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

      <h2 className="mt-8 text-2xl font-bold">每日消费汇总</h2>

      <section className="mt-4 flex max-w-md flex-col gap-4">
        <label className="flex flex-col gap-1 text-sm font-medium">
          查询日期
          <input
            type="date"
            value={summaryDate}
            onChange={(e) => setSummaryDate(e.target.value)}
            className="rounded-lg border px-3 py-2"
          />
        </label>

        <button
          onClick={querySummary}
          className="mt-2 rounded-lg bg-black px-4 py-2 text-white"
        >
          查询汇总
        </button>
      </section>

      {summaryError && (
        <p className="mt-4 text-red-600 font-medium">{summaryError}</p>
      )}

      {summaryResult && (
        <section className="mt-4 rounded-xl border p-4 max-w-md">
          <p>日期：{summaryResult.date}</p>
          <p>消费总额：{summaryResult.total_amount} 元</p>
          <p>消费笔数：{summaryResult.count}</p>
        </section>
      )}

      <hr className="mt-8 max-w-md border-gray-700" />

      <h2 className="mt-8 text-2xl font-bold">消费分类统计</h2>

      <section className="mt-4 flex max-w-md flex-col gap-4">
        <label className="flex flex-col gap-1 text-sm font-medium">
          开始日期
          <input
            type="date"
            value={categoryStartDate}
            onChange={(e) => setCategoryStartDate(e.target.value)}
            className="rounded-lg border px-3 py-2"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm font-medium">
          结束日期
          <input
            type="date"
            value={categoryEndDate}
            onChange={(e) => setCategoryEndDate(e.target.value)}
            className="rounded-lg border px-3 py-2"
          />
        </label>

        <div className="flex gap-2">
          <button
            onClick={() =>
              queryCategorySummaryByRange(
                getTodayLocalDateString(),
                getTodayLocalDateString()
              )
            }
            className="rounded-lg border px-3 py-2 text-sm text-gray-400 hover:text-white"
          >
            查询今日
          </button>
          <button
            onClick={() =>
              queryCategorySummaryByRange(
                getCurrentMonthStartDateString(),
                getTodayLocalDateString()
              )
            }
            className="rounded-lg border px-3 py-2 text-sm text-gray-400 hover:text-white"
          >
            查询本月
          </button>
        </div>

        <button
          onClick={queryCategorySummary}
          className="mt-2 rounded-lg bg-black px-4 py-2 text-white"
        >
          查询分类统计
        </button>
      </section>

      {categoryError && (
        <p className="mt-4 text-red-600 font-medium">{categoryError}</p>
      )}

      {categoryResult && categoryResult.length > 0 && (
        <section className="mt-4 max-w-md flex flex-col gap-3">
          {categoryResult.map((item, index) => (
            <div
              key={index}
              className="rounded-xl border border-gray-700 p-3"
            >
              <p>
                <span className="text-gray-400">分类：</span>
                {item.category}
              </p>
              <p>
                <span className="text-gray-400">总金额：</span>
                {item.total_amount} 元
              </p>
              <p>
                <span className="text-gray-400">笔数：</span>
                {item.count}
              </p>
            </div>
          ))}
        </section>
      )}

      {categoryResult && categoryResult.length === 0 && (
        <p className="mt-4 text-gray-400">该日期范围内暂无消费记录</p>
      )}

      <hr className="mt-8 max-w-md border-gray-700" />

      <h2 className="mt-8 text-2xl font-bold">本月总览</h2>

      <section className="mt-4 flex max-w-md flex-col gap-4">
        <button
          onClick={fetchMonthlySummary}
          className="rounded-lg bg-black px-4 py-2 text-white"
        >
          刷新本月总览
        </button>
      </section>

      {monthlyError && (
        <p className="mt-4 text-red-600 font-medium">{monthlyError}</p>
      )}

      {monthlyResult && monthlyResult.count > 0 && (
        <section className="mt-4 max-w-md rounded-xl border p-4">
          <p>当前月份：{monthlyResult.month}</p>
          <p>本月总消费：{monthlyResult.total_amount} 元</p>
          <p>本月消费笔数：{monthlyResult.count}</p>
          <p>日均消费：{monthlyResult.average_daily_amount} 元</p>

          {monthlyResult.items.length > 0 && (
            <div className="mt-4 flex flex-col gap-3">
              <h3 className="font-semibold text-gray-400">分类明细</h3>
              {monthlyResult.items.map((item, index) => (
                <div
                  key={index}
                  className="rounded-xl border border-gray-700 p-3"
                >
                  <p>
                    <span className="text-gray-400">分类：</span>
                    {item.category}
                  </p>
                  <p>
                    <span className="text-gray-400">总金额：</span>
                    {item.total_amount} 元
                  </p>
                  <p>
                    <span className="text-gray-400">笔数：</span>
                    {item.count}
                  </p>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {monthlyResult && monthlyResult.count === 0 && (
        <p className="mt-4 text-gray-400">本月暂无消费记录</p>
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