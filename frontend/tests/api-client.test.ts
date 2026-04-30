import assert from "node:assert/strict";
import test from "node:test";

import { apiClient, ApiError } from "../app/lib/api-client";

test("api client parses unified error responses", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () =>
    new Response(
      JSON.stringify({
        error: {
          code: "HTTP_404",
          message: "消费记录不存在",
          details: null,
        },
      }),
      { status: 404 }
    );

  try {
    await assert.rejects(
      () => apiClient.health(),
      (error) =>
        error instanceof ApiError &&
        error.status === 404 &&
        error.message === "消费记录不存在"
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("api client falls back when error body is not JSON", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response("not-json", { status: 500 });

  try {
    await assert.rejects(
      () => apiClient.health(),
      (error) =>
        error instanceof ApiError &&
        error.status === 500 &&
        error.message === "请求失败"
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("api client persists saved amount updates", async () => {
  const originalFetch = globalThis.fetch;
  const calls: { url: string; init?: RequestInit }[] = [];
  globalThis.fetch = async (input, init) => {
    calls.push({ url: String(input), init });
    return new Response(JSON.stringify({ id: 7, saved_amount: 12.35 }), { status: 200 });
  };

  try {
    await apiClient.updatePlanSavedAmount(7, 12.35);
  } finally {
    globalThis.fetch = originalFetch;
  }

  assert.equal(calls.length, 1);
  assert.equal(calls[0].url.endsWith("/plans/7"), true);
  assert.equal(calls[0].init?.method, "PUT");
  assert.equal(calls[0].init?.body, JSON.stringify({ saved_amount: 12.35 }));
});
