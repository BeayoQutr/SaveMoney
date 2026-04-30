"use client";

import { useRef, useState } from "react";

import { apiClient } from "../lib/api-client";
import { getUploadFailureMessage } from "../lib/ui-logic";

export function BackupPanel() {
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const restoreInputRef = useRef<HTMLInputElement>(null);
  const csvInputRef = useRef<HTMLInputElement>(null);

  async function handleDownloadDb() {
    setError("");
    setStatus("正在下载数据库备份...");
    setLoading(true);
    try {
      await apiClient.downloadDbBackup();
      setStatus("数据库下载已开始，请查看浏览器下载列表");
    } catch (err) {
      setError(getUploadFailureMessage(err, "下载失败"));
      setStatus("");
    } finally {
      setLoading(false);
    }
  }

  async function handleRestoreDb(file: File) {
    const ok = window.confirm(
      "⚠️ 警告：恢复数据库将覆盖当前所有数据！\n\n" +
        "系统会先自动备份当前数据库，但请确认你选择的文件是正确的备份文件。\n\n" +
        "确定继续吗？"
    );
    if (!ok) return;

    setError("");
    setStatus("正在恢复数据库...");
    setLoading(true);
    try {
      const result = await apiClient.restoreDb(file);
      setStatus(`${result.message}（已自动备份旧库）`);
    } catch (err) {
      setError(getUploadFailureMessage(err, "数据库恢复失败"));
      setStatus("");
    } finally {
      setLoading(false);
      if (restoreInputRef.current) restoreInputRef.current.value = "";
    }
  }

  async function handleImportCsv(file: File) {
    setError("");
    setStatus("正在导入 CSV...");
    setLoading(true);
    try {
      const result = await apiClient.importCsv(file);
      setStatus(`${result.message}（已自动备份旧库）`);
    } catch (err) {
      setError(getUploadFailureMessage(err, "CSV 导入失败"));
      setStatus("");
    } finally {
      setLoading(false);
      if (csvInputRef.current) csvInputRef.current.value = "";
    }
  }

  return (
    <section className="rounded-lg border border-gray-800 bg-gray-950 p-4 shadow-sm sm:p-5">
      <div className="flex flex-col gap-1">
        <p className="text-sm text-emerald-300">数据安全</p>
        <h2 className="text-xl font-bold">备份与恢复</h2>
        <p className="text-sm text-gray-400">
          <span className="font-semibold text-yellow-300">迁移或重装环境前，务必先下载数据库备份！</span>
        </p>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <button
          type="button"
          disabled={loading}
          onClick={() => void handleDownloadDb()}
          className="min-h-12 rounded-lg bg-emerald-500 px-4 font-semibold text-black disabled:opacity-60"
        >
          下载数据库备份
        </button>

        <button
          type="button"
          disabled={loading}
          onClick={() => restoreInputRef.current?.click()}
          className="min-h-12 rounded-lg border border-yellow-600 px-4 font-medium text-yellow-200 disabled:opacity-60"
        >
          从备份文件恢复
        </button>
        <input
          ref={restoreInputRef}
          type="file"
          accept=".db"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleRestoreDb(file);
          }}
        />

        <button
          type="button"
          disabled={loading}
          onClick={() => csvInputRef.current?.click()}
          className="min-h-12 rounded-lg border border-gray-600 px-4 font-medium disabled:opacity-60"
        >
          导入 CSV
        </button>
        <input
          ref={csvInputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleImportCsv(file);
          }}
        />
      </div>

      {status && <p className="mt-3 rounded-lg bg-emerald-950 px-3 py-2 text-sm">{status}</p>}
      {error && <p className="mt-3 rounded-lg bg-red-950 px-3 py-2 text-sm">{error}</p>}
    </section>
  );
}
