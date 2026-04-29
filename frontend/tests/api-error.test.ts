import assert from "node:assert/strict";
import test from "node:test";

import { getApiErrorMessage } from "../app/lib/api-error";

test("reads unified API error messages", () => {
  assert.equal(
    getApiErrorMessage({
      error: {
        code: "VALIDATION_ERROR",
        message: "请求参数校验失败",
        details: [],
      },
    }),
    "请求参数校验失败"
  );
});

test("keeps compatibility with legacy detail string errors", () => {
  assert.equal(getApiErrorMessage({ detail: "消费记录不存在" }), "消费记录不存在");
});

test("returns null for unknown error shapes", () => {
  assert.equal(getApiErrorMessage({ detail: [{ msg: "bad" }] }), null);
  assert.equal(getApiErrorMessage(null), null);
});
