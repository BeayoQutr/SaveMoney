"use client";

import { useState } from "react";

import { BackendStatus } from "./components/BackendStatus";
import { ExportPanel } from "./components/ExportPanel";
import { ExpenseForm } from "./components/ExpenseForm";
import { ExpenseList } from "./components/ExpenseList";
import { MonthlySummary } from "./components/MonthlySummary";
import { PlanForm } from "./components/PlanForm";

export default function Home() {
  const [refreshKey, setRefreshKey] = useState(0);

  function notifyDataChanged() {
    setRefreshKey((value) => value + 1);
  }

  return (
    <main className="min-h-screen bg-black px-4 py-5 text-gray-100 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-5">
        <header className="grid gap-3">
          <h1 className="text-3xl font-bold">SaveMoney AI</h1>
          <p className="max-w-2xl text-sm leading-6 text-gray-300">
            个人攒钱计划和消费记录助手。普通记账功能可离线使用，AI 功能在配置
            DeepSeek API Key 后启用。
          </p>
        </header>

        <BackendStatus />

        <section className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(360px,420px)]">
          <div className="grid gap-5">
            <ExpenseForm onChanged={notifyDataChanged} />
            <MonthlySummary refreshKey={refreshKey} />
          </div>

          <div className="grid content-start gap-5">
            <ExpenseList refreshKey={refreshKey} onChanged={notifyDataChanged} />
            <ExportPanel />
          </div>
        </section>

        <PlanForm />

        <section className="rounded-lg border border-gray-800 p-4 text-sm text-gray-300">
          <h2 className="font-semibold text-gray-100">数据存储说明</h2>
          <p className="mt-2">消费记录保存在本地 SQLite 数据库中，默认文件为 backend/savemoney.db。</p>
          <p>常用信息保存在浏览器 localStorage 中，CSV 导出可作为消费记录备份。</p>
        </section>

        <p className="pb-4 text-center text-xs text-gray-500">作者：岁年</p>
      </div>
    </main>
  );
}
