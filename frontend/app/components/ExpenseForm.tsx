"use client";

import { useState } from "react";

import { apiClient, ApiError } from "../lib/api-client";
import { validateExpenseForm } from "../lib/ui-logic";

const quickNotes = ["早餐", "午餐", "晚餐", "公交", "地铁", "学习", "买药", "购物"];
const categories = ["餐饮", "交通", "学习", "娱乐", "购物", "医疗", "生活", "其他"];
const paymentMethods = ["微信", "支付宝", "现金", "银行卡", "信用卡"];

function getTodayLocalDateString() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getApiMessage(error: unknown, fallback: string) {
  if (error instanceof ApiError) {
    if (error.status === 502) {
      return "AI 服务暂时不可用，普通记账仍可继续使用";
    }
    return error.message || fallback;
  }
  return fallback;
}

type ExpenseFormProps = {
  onChanged: () => void;
};

export function ExpenseForm({ onChanged }: ExpenseFormProps) {
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  const [date, setDate] = useState(getTodayLocalDateString());
  const [category, setCategory] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("");
  const [isNecessary, setIsNecessary] = useState<number | "">("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [aiReason, setAiReason] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [noteLoading, setNoteLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  function resetAiState() {
    setCategory("");
    setAiReason("");
  }

  function resetForm() {
    setAmount("");
    setNote("");
    setCategory("");
    setPaymentMethod("");
    setIsNecessary("");
    setAiReason("");
  }

  async function suggestCategory() {
    setError("");
    setSuccess("");
    const amountNum = Number(amount);
    if (!amount || Number.isNaN(amountNum) || amountNum <= 0) {
      setError("金额非法，请输入大于 0 的数字");
      return;
    }
    if (!note.trim()) {
      setError("备注不能为空，请填写这笔钱花在哪里");
      return;
    }

    setAiLoading(true);
    try {
      const data = await apiClient.suggestCategory(amountNum, note.trim());
      setCategory(data.category);
      setAiReason(data.reason);
      setSuccess("已生成分类建议");
    } catch (err) {
      setError(getApiMessage(err, "AI 分类建议生成失败，请稍后重试"));
    } finally {
      setAiLoading(false);
    }
  }

  async function optimizeNote() {
    setError("");
    setSuccess("");
    if (!note.trim()) {
      setError("备注不能为空，请先输入要优化的备注");
      return;
    }

    setNoteLoading(true);
    try {
      const data = await apiClient.optimizeNote(note.trim());
      setNote(data.optimized_note);
      resetAiState();
      setSuccess("备注已优化");
    } catch (err) {
      setError(getApiMessage(err, "AI 备注优化失败，请稍后重试"));
    } finally {
      setNoteLoading(false);
    }
  }

  async function recordExpense() {
    setError("");
    setSuccess("");
    const amountNum = Number(amount);
    const validationError = validateExpenseForm({ amount, note, date });
    if (validationError) {
      setError(validationError);
      return;
    }

    setSaving(true);
    try {
      const result = await apiClient.createExpense({
        amount: amountNum,
        note: note.trim(),
        date,
        category: category || undefined,
        payment_method: paymentMethod || undefined,
        is_necessary: isNecessary !== "" ? isNecessary : undefined,
      });
      resetForm();
      setSuccess(`${result.message}：${result.amount} 元，${result.category}`);
      onChanged();
    } catch (err) {
      setError(getApiMessage(err, "记录失败，请确认后端已启动"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="rounded-lg border border-gray-800 bg-gray-950 p-4 shadow-sm sm:p-5">
      <div className="flex flex-col gap-1">
        <p className="text-sm text-emerald-300">快速记账</p>
        <h2 className="text-2xl font-bold">记一笔消费</h2>
      </div>

      <div className="mt-4 grid gap-4">
        <label className="grid gap-1 text-sm font-medium">
          消费金额
          <input
            type="number"
            inputMode="decimal"
            value={amount}
            onChange={(event) => {
              setAmount(event.target.value);
              resetAiState();
            }}
            className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3 text-base"
            placeholder="例如 35.50"
          />
        </label>

        <label className="grid gap-1 text-sm font-medium">
          消费备注
          <input
            type="text"
            value={note}
            onChange={(event) => {
              setNote(event.target.value);
              resetAiState();
            }}
            className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3 text-base"
            placeholder="例如 午餐"
          />
        </label>

        <div className="flex flex-wrap gap-2">
          {quickNotes.map((label) => (
            <button
              key={label}
              type="button"
              onClick={() => {
                setNote(label);
                resetAiState();
              }}
              className="min-h-10 rounded-lg border border-gray-700 px-3 text-sm text-gray-200"
            >
              {label}
            </button>
          ))}
        </div>

        <label className="grid gap-1 text-sm font-medium">
          分类
          <select
            value={category}
            onChange={(event) => setCategory(event.target.value)}
            className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3 text-base"
          >
            <option value="">自动判断或选择分类</option>
            {categories.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <label className="grid gap-1 text-sm font-medium">
          消费日期
          <input
            type="date"
            value={date}
            onChange={(event) => setDate(event.target.value)}
            className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3 text-base"
          />
        </label>

        <label className="grid gap-1 text-sm font-medium">
          支付方式
          <select
            value={paymentMethod}
            onChange={(event) => setPaymentMethod(event.target.value)}
            className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3 text-base"
          >
            <option value="">选择支付方式（可选）</option>
            {paymentMethods.map((method) => (
              <option key={method} value={method}>
                {method}
              </option>
            ))}
          </select>
        </label>

        <label className="flex items-center gap-3 text-sm font-medium">
          <input
            type="checkbox"
            checked={isNecessary === 1}
            onChange={(event) => setIsNecessary(event.target.checked ? 1 : 0)}
            className="h-5 w-5 rounded border-gray-700 bg-gray-900"
          />
          必要消费
        </label>

        <div className="grid gap-2 sm:grid-cols-3">
          <button
            type="button"
            onClick={recordExpense}
            disabled={saving}
            className="min-h-12 rounded-lg bg-emerald-500 px-4 font-semibold text-black disabled:opacity-60"
          >
            {saving ? "保存中..." : "保存消费"}
          </button>
          <button
            type="button"
            onClick={suggestCategory}
            disabled={aiLoading}
            className="min-h-12 rounded-lg border border-gray-600 px-4 font-medium disabled:opacity-60"
          >
            {aiLoading ? "分类中..." : "AI 建议分类"}
          </button>
          <button
            type="button"
            onClick={optimizeNote}
            disabled={noteLoading}
            className="min-h-12 rounded-lg border border-gray-600 px-4 font-medium disabled:opacity-60"
          >
            {noteLoading ? "优化中..." : "AI 优化备注"}
          </button>
        </div>

        {category && (
          <p className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm">
            当前分类：{category}
            {aiReason ? `。${aiReason}` : ""}
          </p>
        )}
        {success && <p className="rounded-lg bg-emerald-950 px-3 py-2 text-sm">{success}</p>}
        {error && <p className="rounded-lg bg-red-950 px-3 py-2 text-sm">{error}</p>}
      </div>
    </section>
  );
}
