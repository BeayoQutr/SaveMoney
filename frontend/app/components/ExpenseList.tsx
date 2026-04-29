"use client";

import { useCallback, useEffect, useState } from "react";

import { apiClient, ApiError } from "../lib/api-client";
import { ExpenseItem } from "../types";

const categories = ["餐饮", "交通", "学习", "娱乐", "购物", "医疗", "生活", "其他"];
const paymentMethods = ["微信", "支付宝", "现金", "银行卡", "信用卡"];

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof ApiError ? error.message || fallback : fallback;
}

type ExpenseListProps = {
  refreshKey: number;
  onChanged: () => void;
};

export function ExpenseList({ refreshKey, onChanged }: ExpenseListProps) {
  const [items, setItems] = useState<ExpenseItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editAmount, setEditAmount] = useState("");
  const [editNote, setEditNote] = useState("");
  const [editDate, setEditDate] = useState("");
  const [editCategory, setEditCategory] = useState("");
  const [editPaymentMethod, setEditPaymentMethod] = useState("");
  const [editIsNecessary, setEditIsNecessary] = useState<number | "">("");

  // Filters
  const [filterStartDate, setFilterStartDate] = useState("");
  const [filterEndDate, setFilterEndDate] = useState("");
  const [filterCategory, setFilterCategory] = useState("");
  const [filterKeyword, setFilterKeyword] = useState("");
  const [pageOffset, setPageOffset] = useState(0);
  const pageLimit = 20;

  const fetchExpenses = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await apiClient.listExpenses({
        startDate: filterStartDate || undefined,
        endDate: filterEndDate || undefined,
        category: filterCategory || undefined,
        keyword: filterKeyword || undefined,
        limit: pageLimit,
        offset: pageOffset,
      });
      setItems(result.items);
      setTotal(result.total);
    } catch (err) {
      setError(getErrorMessage(err, "消费记录加载失败，请确认后端已启动"));
    } finally {
      setLoading(false);
    }
  }, [filterStartDate, filterEndDate, filterCategory, filterKeyword, pageOffset]);

  useEffect(() => {
    void Promise.resolve().then(fetchExpenses);
  }, [fetchExpenses, refreshKey]);

  function startEdit(item: ExpenseItem) {
    setEditingId(item.id);
    setEditAmount(String(item.amount));
    setEditNote(item.note);
    setEditDate(item.date);
    setEditCategory(item.category);
    setEditPaymentMethod(item.payment_method || "");
    setEditIsNecessary(item.is_necessary !== null ? item.is_necessary : "");
    setError("");
    setMessage("");
  }

  async function saveEdit(id: number) {
    setError("");
    setMessage("");
    const amount = Number(editAmount);
    if (!editAmount || Number.isNaN(amount) || amount <= 0) {
      setError("金额非法，请输入大于 0 的数字");
      return;
    }
    if (!editNote.trim()) {
      setError("备注不能为空");
      return;
    }
    if (!editDate) {
      setError("请选择消费日期");
      return;
    }

    try {
      await apiClient.updateExpense(id, {
        amount,
        note: editNote.trim(),
        date: editDate,
        category: editCategory || undefined,
        payment_method: editPaymentMethod || undefined,
        is_necessary: editIsNecessary !== "" ? editIsNecessary : undefined,
      });
      setEditingId(null);
      setMessage("消费记录已更新");
      await fetchExpenses();
      onChanged();
    } catch (err) {
      setError(getErrorMessage(err, "更新失败，请确认后端已启动或记录是否仍然存在"));
    }
  }

  async function deleteExpense(id: number) {
    setError("");
    setMessage("");
    const ok = window.confirm("确定删除这条消费记录吗？删除后无法恢复。");
    if (!ok) {
      return;
    }

    try {
      await apiClient.deleteExpense(id);
      setMessage("消费记录已删除");
      await fetchExpenses();
      onChanged();
    } catch (err) {
      setError(getErrorMessage(err, "删除失败，请确认后端已启动或记录是否仍然存在"));
    }
  }

  function applyFilters() {
    setPageOffset(0);
    void fetchExpenses();
  }

  function clearFilters() {
    setFilterStartDate("");
    setFilterEndDate("");
    setFilterCategory("");
    setFilterKeyword("");
    setPageOffset(0);
  }

  const totalPages = Math.ceil(total / pageLimit);
  const currentPage = Math.floor(pageOffset / pageLimit) + 1;

  return (
    <section className="rounded-lg border border-gray-800 p-4 sm:p-5">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-xl font-bold">消费记录</h2>
        <button
          type="button"
          onClick={() => void fetchExpenses()}
          className="min-h-11 rounded-lg border border-gray-600 px-4 font-medium"
        >
          {loading ? "刷新中..." : "刷新列表"}
        </button>
      </div>

      {/* Filter bar */}
      <div className="mt-4 grid gap-3 rounded-lg border border-gray-800 bg-gray-950 p-3 sm:grid-cols-2 lg:grid-cols-4">
        <label className="grid gap-1 text-sm">
          开始日期
          <input
            type="date"
            value={filterStartDate}
            onChange={(e) => setFilterStartDate(e.target.value)}
            className="min-h-10 rounded-lg border border-gray-700 bg-gray-900 px-3 text-sm"
          />
        </label>
        <label className="grid gap-1 text-sm">
          结束日期
          <input
            type="date"
            value={filterEndDate}
            onChange={(e) => setFilterEndDate(e.target.value)}
            className="min-h-10 rounded-lg border border-gray-700 bg-gray-900 px-3 text-sm"
          />
        </label>
        <label className="grid gap-1 text-sm">
          分类
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="min-h-10 rounded-lg border border-gray-700 bg-gray-900 px-3 text-sm"
          >
            <option value="">全部分类</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </label>
        <label className="grid gap-1 text-sm">
          关键词搜索
          <input
            type="text"
            value={filterKeyword}
            onChange={(e) => setFilterKeyword(e.target.value)}
            className="min-h-10 rounded-lg border border-gray-700 bg-gray-900 px-3 text-sm"
            placeholder="输入备注关键词"
          />
        </label>
        <div className="flex gap-2 sm:col-span-2 lg:col-span-4">
          <button
            type="button"
            onClick={applyFilters}
            className="min-h-10 rounded-lg bg-emerald-500 px-4 text-sm font-semibold text-black"
          >
            筛选
          </button>
          <button
            type="button"
            onClick={clearFilters}
            className="min-h-10 rounded-lg border border-gray-600 px-4 text-sm font-medium"
          >
            清除筛选
          </button>
        </div>
      </div>

      {message && <p className="mt-3 rounded-lg bg-emerald-950 px-3 py-2 text-sm">{message}</p>}
      {error && <p className="mt-3 rounded-lg bg-red-950 px-3 py-2 text-sm">{error}</p>}

      <div className="mt-4 grid gap-3">
        {!loading && items.length === 0 && (
          <p className="rounded-lg bg-gray-900 px-3 py-3 text-sm text-gray-300">暂无消费记录</p>
        )}

        {items.map((item) => (
          <article key={item.id} className="rounded-lg border border-gray-800 bg-gray-950 p-4">
            {editingId === item.id ? (
              <div className="grid gap-3">
                <input
                  type="number"
                  value={editAmount}
                  onChange={(event) => setEditAmount(event.target.value)}
                  className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3"
                  placeholder="金额"
                />
                <input
                  type="text"
                  value={editNote}
                  onChange={(event) => setEditNote(event.target.value)}
                  className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3"
                  placeholder="备注"
                />
                <input
                  type="date"
                  value={editDate}
                  onChange={(event) => setEditDate(event.target.value)}
                  className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3"
                />
                <select
                  value={editCategory}
                  onChange={(event) => setEditCategory(event.target.value)}
                  className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3"
                >
                  {categories.map((category) => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
                <select
                  value={editPaymentMethod}
                  onChange={(event) => setEditPaymentMethod(event.target.value)}
                  className="min-h-12 rounded-lg border border-gray-700 bg-gray-900 px-3"
                >
                  <option value="">选择支付方式（可选）</option>
                  {paymentMethods.map((method) => (
                    <option key={method} value={method}>
                      {method}
                    </option>
                  ))}
                </select>
                <label className="flex items-center gap-3 text-sm">
                  <input
                    type="checkbox"
                    checked={editIsNecessary === 1}
                    onChange={(event) => setEditIsNecessary(event.target.checked ? 1 : 0)}
                    className="h-5 w-5 rounded border-gray-700 bg-gray-900"
                  />
                  必要消费
                </label>
                <div className="grid gap-2 sm:grid-cols-2">
                  <button
                    type="button"
                    onClick={() => void saveEdit(item.id)}
                    className="min-h-11 rounded-lg bg-white px-4 font-semibold text-black"
                  >
                    保存修改
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditingId(null)}
                    className="min-h-11 rounded-lg border border-gray-600 px-4 font-medium"
                  >
                    取消
                  </button>
                </div>
              </div>
            ) : (
              <div className="grid gap-3">
                <div>
                  <p className="text-lg font-semibold">{item.amount} 元</p>
                  <p className="text-sm text-gray-300">{item.note}</p>
                  <p className="text-sm text-gray-400">
                    {item.date} · {item.category}
                    {item.payment_method ? ` · ${item.payment_method}` : ""}
                    {item.is_necessary === 1 ? " · 必要" : item.is_necessary === 0 ? " · 非必要" : ""}
                  </p>
                </div>
                <div className="grid gap-2 sm:grid-cols-2">
                  <button
                    type="button"
                    onClick={() => startEdit(item)}
                    className="min-h-11 rounded-lg border border-gray-600 px-4 font-medium"
                  >
                    编辑
                  </button>
                  <button
                    type="button"
                    onClick={() => void deleteExpense(item.id)}
                    className="min-h-11 rounded-lg border border-red-700 px-4 font-medium text-red-100"
                  >
                    删除这条记录
                  </button>
                </div>
              </div>
            )}
          </article>
        ))}
      </div>

      {/* Pagination */}
      {total > 0 && (
        <div className="mt-4 flex items-center justify-between rounded-lg border border-gray-800 bg-gray-950 px-4 py-3 text-sm">
          <span className="text-gray-400">
            共 {total} 条记录，第 {currentPage} / {totalPages} 页
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={pageOffset === 0}
              onClick={() => {
                setPageOffset(Math.max(0, pageOffset - pageLimit));
              }}
              className="min-h-10 rounded-lg border border-gray-600 px-3 disabled:opacity-40"
            >
              上一页
            </button>
            <button
              type="button"
              disabled={pageOffset + pageLimit >= total}
              onClick={() => {
                setPageOffset(pageOffset + pageLimit);
              }}
              className="min-h-10 rounded-lg border border-gray-600 px-3 disabled:opacity-40"
            >
              下一页
            </button>
          </div>
        </div>
      )}
    </section>
  );
}