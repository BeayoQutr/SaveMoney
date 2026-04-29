"use client";

import { useCallback, useEffect, useState } from "react";

import { apiClient } from "../lib/api-client";

export function BackendStatus() {
  const [online, setOnline] = useState<boolean | null>(null);
  const [aiReady, setAiReady] = useState<boolean | null>(null);
  const [message, setMessage] = useState("正在检测后端连接...");

  const checkBackend = useCallback(async () => {
    setOnline(null);
    setAiReady(null);
    setMessage("正在检测后端连接...");
    try {
      await apiClient.health();
      setOnline(true);
      try {
        const ai = await apiClient.aiStatus();
        setAiReady(ai.ai_configured);
      } catch {
        setAiReady(false);
      }
      setMessage("后端已连接，可以正常记账");
    } catch {
      setOnline(false);
      setMessage("后端未响应，请先启动 FastAPI 服务");
    }
  }, []);

  useEffect(() => {
    void Promise.resolve().then(checkBackend);
  }, [checkBackend]);

  const statusClass =
    online === true
      ? "border-emerald-700 bg-emerald-950/40 text-emerald-100"
      : online === false
      ? "border-red-800 bg-red-950/40 text-red-100"
      : "border-gray-700 bg-gray-900 text-gray-200";

  return (
    <section className={`rounded-lg border px-4 py-3 text-sm ${statusClass}`}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p>
            <span className="font-semibold">连接状态：</span>
            {message}
          </p>
          {online === true && aiReady !== null && (
            <p className="mt-1 text-xs">
              {aiReady ? "🤖 AI 功能已就绪" : "⚠️ AI 未配置（DeepSeek Key 缺失）— 普通记账正常可用"}
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={() => void checkBackend()}
          className="min-h-11 rounded-lg border border-current px-4 py-2 font-medium"
        >
          重新检测
        </button>
      </div>
    </section>
  );
}
