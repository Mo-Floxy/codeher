/**
 * JavaScript execution inside a `node:vm` context.
 *
 * The learner's source is compiled as a Script and run against a context object
 * that only exposes safe globals. There is no require(), no process and no
 * fetch, so a submission cannot reach the filesystem or the network. The
 * interrupt budget is enforced by V8's own timeout, which stops an infinite
 * loop without killing the runner process.
 */

const vm = require("node:vm");

const { deepEqual, toDisplay } = require("./compare");

const IDENTIFIER = /^[A-Za-z_$][A-Za-z0-9_$]*$/;

const SAFE_GLOBALS = {
  Array,
  Object,
  JSON,
  Map,
  Set,
  WeakMap,
  WeakSet,
  Promise,
  Symbol,
  Math,
  Number,
  String,
  Boolean,
  Date,
  RegExp,
  Error,
  TypeError,
  RangeError,
  SyntaxError,
  isNaN,
  isFinite,
  parseInt,
  parseFloat,
  encodeURIComponent,
  decodeURIComponent,
};

function buildContext() {
  const sandbox = { ...SAFE_GLOBALS };
  // Console output from submissions is discarded rather than forwarded: the API
  // response is the only channel back to the browser.
  sandbox.console = { log() {}, error() {}, warn() {}, info() {}, debug() {}, table() {} };
  return vm.createContext(sandbox, { name: "codeher-submission" });
}

function resolveFunction(context, source, functionName) {
  // The name is validated as a bare identifier by the server before it reaches
  // here, so it is safe to splice into the bridge statement.
  if (!IDENTIFIER.test(functionName)) throw new Error("The function name is not a valid identifier.");
  const bridge = `\n;globalThis["__submitted"] = (typeof ${functionName} === "function") ? ${functionName} : undefined;\n`;
  vm.runInContext(source + bridge, context, { filename: "submission.js", timeout: 1000 });
  const fn = context.__submitted;
  if (typeof fn !== "function") {
    throw new Error(
      `No function named "${functionName}" was found. Define it and return a value from it.`
    );
  }
  return fn;
}

function runJavaScript({ code, functionName, tests, timeLimitMs }) {
  const context = buildContext();
  const startedAt = process.hrtime.bigint();
  const results = [];
  let loadError = null;

  try {
    resolveFunction(context, code, functionName || "solution");
  } catch (error) {
    loadError = describe(error);
  }

  if (loadError) {
    return {
      ok: false,
      error: loadError,
      runtime_ms: elapsedMs(startedAt),
      results: (tests || []).map((test) => ({
        name: test.name,
        passed: false,
        expected: toDisplay(test.expected),
        actual: null,
        error: loadError,
      })),
    };
  }

  for (const test of tests) {
    const entry = { name: test.name, passed: false, expected: toDisplay(test.expected), actual: null, error: "" };
    try {
      context.__args = test.args || [];
      const value = vm.runInContext("__result = __submitted(...__args);", context, {
        filename: "harness.js",
        timeout: Math.max(100, timeLimitMs || 2000),
      });
      entry.actual = toDisplay(value === undefined ? context.__result : value);
      entry.passed = deepEqual(context.__result, test.expected);
    } catch (error) {
      const message = describe(error);
      entry.error = message;
      if (!message) entry.error = "Your function did not return before the time limit.";
    }
    results.push(entry);
  }

  const passed = results.filter((result) => result.passed).length;
  return { ok: passed === results.length, runtime_ms: elapsedMs(startedAt), results };
}

function describe(error) {
  if (!error) return "";
  const text = String(error.message || error);
  if (/Script execution timed out/.test(text)) return "";
  return text.split("\n").slice(0, 3).join(" ").slice(0, 400);
}

function elapsedMs(startedAt) {
  return Number(process.hrtime.bigint() - startedAt) / 1e6;
}

module.exports = { runJavaScript };
