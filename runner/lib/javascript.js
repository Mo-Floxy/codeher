/**
 * JavaScript execution: a throwaway `node` process per submission, and inside it
 * a fresh `node:vm` context.
 *
 * Neither layer is sufficient on its own. `node:vm` is not a security boundary,
 * and the way it leaks is easy to overlook: anything this process *assigns* into
 * the sandbox arrives with its host realm attached, so injecting `Object`, `JSON`
 * or `Array` here — or a `console` stub, or a test's arguments array — handed the
 * submission a host `Function` constructor, which is one call away from `process`
 * and `require`. So the context is created empty (a new realm already has every
 * standard built-in) and the stubs and arguments are built by evaluating text
 * *inside* it.
 *
 * The process is the backstop for whatever still escapes the realm: it starts with
 * an environment that holds no credentials, is denied `child_process` by Node's
 * permission model where that model exists, and is killed when it overruns.
 */

const path = require("node:path");
const { spawn, spawnSync } = require("node:child_process");

const vm = require("node:vm");

const { deepEqual, toDisplay } = require("./compare");
const { minimalEnv } = require("./python");

const HARNESS = path.join(__dirname, "javascript_harness.js");
const IDENTIFIER = /^[A-Za-z_$][A-Za-z0-9_$]*$/;

const REALM_PREAMBLE = `
var console = { log: function () {}, error: function () {}, warn: function () {}, info: function () {}, debug: function () {}, table: function () {} };
var __result;
`;

/**
 * `--permission` arrived in Node 20 and is refused outright by older runtimes, so
 * it is detected once instead of assumed: a runner that cannot start its sandbox
 * must still grade submissions, just with one less layer. The child never probes —
 * it is already inside the model, and asking again would just hit a denied spawn.
 */
const supportsPermissionModel = (() => {
  if (process.env.CODEHER_JS_SANDBOX_CHILD === "1") return false;
  try {
    return spawnSync(process.execPath, ["--permission", "-e", "0"], { encoding: "utf8", timeout: 8000 }).status === 0;
  } catch {
    return false;
  }
})();

function buildContext() {
  // A null-prototype sandbox object: contextifying it exposes nothing, and the new
  // realm's own intrinsics are what the submission sees.
  const context = vm.createContext(Object.create(null), { name: "codeher-submission" });
  vm.runInContext(REALM_PREAMBLE, context, { filename: "harness.js", timeout: 1000 });
  return context;
}

/**
 * Rebuild a JSON value inside the sandbox realm.
 *
 * The obvious `context.__args = test.args` copies a host array whose
 * `.constructor.constructor` is the host `Function`; parsing the same text with
 * the realm's own `JSON.parse` produces values that can only reach the realm's
 * own intrinsics.
 */
function toRealmValue(context, value) {
  const text = JSON.stringify(value === undefined ? [] : value);
  return vm.runInContext(`JSON.parse(${JSON.stringify(text)})`, context, { filename: "harness.js", timeout: 1000 });
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
      context.__args = toRealmValue(context, test.args);
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

/**
 * Run one submission in a child process and read the report back.
 *
 * The contract with server.js matches lib/python.js deliberately: a submission
 * that cannot be executed comes back as a report with `error` set, never as a
 * crashed runner.
 */
function runJavaScriptIsolated({ code, functionName, tests, timeLimitMs, memoryLimitMb }) {
  const budgetMs = Math.min(60000, Math.max(1000, timeLimitMs || 2000) * Math.max(1, (tests || []).length) + 3000);
  const job = JSON.stringify({
    code,
    function_name: functionName,
    tests,
    time_limit_ms: timeLimitMs,
    memory_limit_mb: memoryLimitMb,
  });

  return new Promise((resolve) => {
    let settled = false;
    const finish = (payload) => {
      if (settled) return;
      settled = true;
      resolve(payload);
    };

    const child = spawn(process.execPath, sandboxArgs(memoryLimitMb).concat(HARNESS), {
      env: Object.assign(minimalEnv(), { CODEHER_JS_SANDBOX_CHILD: "1" }),
      cwd: __dirname,
      windowsHide: true,
      stdio: ["pipe", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout = (stdout + chunk.toString()).slice(-2_000_000);
    });
    child.stderr.on("data", (chunk) => {
      stderr = (stderr + chunk.toString()).slice(-4000);
    });

    // The submission is only ever written to the child's stdin; a sandbox that
    // escapes has no file of ours to touch.
    child.stdin.on("error", () => {});
    child.stdin.end(job);

    const killer = setTimeout(() => {
      child.kill("SIGKILL");
      finish({
        ok: false,
        error: `Your code ran longer than the ${Math.round(budgetMs / 1000)}s budget and was stopped.`,
        runtime_ms: budgetMs,
        results: (tests || []).map((test) => ({
          name: test.name,
          passed: false,
          expected: toDisplay(test.expected),
          actual: null,
          error: "Timed out.",
        })),
      });
    }, budgetMs);

    child.on("error", (error) => {
      clearTimeout(killer);
      finish(unavailable(`Could not start the JavaScript sandbox: ${error.message}`));
    });

    child.on("close", (exitCode) => {
      clearTimeout(killer);
      let report;
      try {
        report = JSON.parse(stdout);
      } catch {
        finish(
          unavailable(
            `The JavaScript sandbox stopped before it could report (exit ${exitCode}).` +
              (stderr ? ` It said: ${stderr.replace(/\s+/g, " ").slice(0, 300)}` : "")
          )
        );
        return;
      }
      if (stderr.trim()) {
        // Warnings (the permission model is flagged experimental) stay in the log,
        // not in the learner's feedback.
        console.warn(`[runner] javascript sandbox stderr: ${stderr.replace(/\s+/g, " ").slice(0, 300)}`);
      }
      finish(report);
    });
  });
}

/**
 * `--permission` with read-only filesystem access is the layer that survives a
 * realm escape: `child_process`, workers and every write are denied by the runtime
 * itself. Reads stay allowed because module loading walks realpaths that a
 * directory-scoped pattern cannot reliably cover, and because on a deployed runner
 * the files hold no secret — the credentials are environment values, and those are
 * stripped before the child starts.
 */
function sandboxArgs(memoryLimitMb) {
  const flags = [`--max-old-space-size=${Math.min(512, Math.max(32, Number(memoryLimitMb) || 128))}`];
  return supportsPermissionModel ? flags.concat("--permission", "--allow-fs-read=*") : flags;
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

function unavailable(message) {
  return { ok: false, error: message, runtime_ms: 0, results: [] };
}

module.exports = { runJavaScript, runJavaScriptIsolated, supportsPermissionModel };
