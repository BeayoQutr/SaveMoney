"use client";

import { useState } from "react";

import { Preset } from "../types";

const STORAGE_KEY = "savemoney_preset";

const defaultPreset: Preset = {
  monthlyIncome: "",
  fixedExpenses: "",
  minimumLivingCost: "",
  identity: "student",
};

function loadPreset(): Preset {
  if (typeof window === "undefined") {
    return defaultPreset;
  }

  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) {
      return defaultPreset;
    }
    const parsed = JSON.parse(saved) as Partial<Preset>;
    return {
      monthlyIncome: parsed.monthlyIncome || "",
      fixedExpenses: parsed.fixedExpenses || "",
      minimumLivingCost: parsed.minimumLivingCost || "",
      identity: parsed.identity || "student",
    };
  } catch {
    return defaultPreset;
  }
}

export function usePreset() {
  const [preset, setPreset] = useState<Preset>(loadPreset);
  const [message, setMessage] = useState("");

  function setField<K extends keyof Preset>(key: K, value: Preset[K]) {
    setPreset((current) => ({ ...current, [key]: value }));
    setMessage("");
  }

  function savePreset() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(preset));
      setMessage("常用信息已保存");
    } catch {
      setMessage("保存失败，请检查浏览器设置");
    }
  }

  function clearPreset() {
    try {
      localStorage.removeItem(STORAGE_KEY);
      setPreset(defaultPreset);
      setMessage("常用信息已清除");
    } catch {
      setMessage("清除失败，请检查浏览器设置");
    }
  }

  return { preset, setField, savePreset, clearPreset, message };
}
