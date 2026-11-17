/**
 * CodeHer runner — a separate process for executing learner code.
 *
 * Django never evals submission code in its own process. It POSTs to
 * /run here, authenticated by a shared secret, and this service answers with a
 * pass/fail report.
 *
 * Start it (from codeher/runner):
 *   $env:RUNNER_SHARED_SECRET = "dev-runner-secret"
 *   npm start
 *
 * Read runner/README.md before exposing this to anything other than localhost.
 */

const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");
const { spawn } = require("node:child_process");

const { runJavaScript } = require("./lib/javascript");
const { runPython, minimalEnv } = require("./lib/python");

loadDotEnv(path.join(__dirname, ".env"));

// Render and friends inject PORT and expect a listener on 0.0.0.0; the explicit
// RUNNER_* names stay authoritative for local development.
const PORT = Number(process.env.RUNNER_PORT || process.env.PORT || 8090);
const HOST = process.env.RUNNER_HOST || "127.0.0.1";
const SECRET = process.env.RUNNER_SHARED_SECRET || "";
const PYTHON_BIN = process.env.PYTHON_BIN || "python";
const MAX_CODE_BYTES = Number(process.env.RUNNER_MAX_CODE_BYTES || 20000);
const MAX_BODY_BYTES = 128 * 1024;
const ALLOWED_LANGUAGES = new Set(["javascript", "python"]);
const IDENTIFIER = /^[A-Za-z_$][A-Za-z0-9_$]*$/;

if (!SECRET) {
  console.error(
    "[runner] RUNNER_SHARED_SECRET is not set. Refusing to start: without it, every request would be trusted."
  );
  process.exit(1);
}

const pythonHealth = { available: false, error: null, version: null };

const server = http.createServer(async (request, response) => {
  const url = new URL(request.url, `http://${request.headers.host || "localhost"}`);

  if (request.method === "GET" && url.pathname === "/health") {
    return json(response, 200, {
      ok: true,
      service: "codeher-runner",
      languages: [...ALLOWED_LANGUAGES],
      max_code_bytes: MAX_CODE_BYTES,
      python: pythonHealth,
    });
  }

  if (request.method !== "POST" || url.pathname !== "/run") {
    return json(response, 404, { ok: false, error: "Unknown route." });
  }

  if (!timingSafeEquals(header(request, "x-runner-secret"), SECRET)) {
    return json(response, 401, { ok: false, error: "Missing or incorrect X-Runner-Secret." });
  }

  let payload;
  try {
    payload = JSON.parse(await readBody(request));
  } catch (error) {
    return json(response, error.statusCode || 400, { ok: false, error: error.message });
  }

  const problem = validate(payload);
  if (problem) return json(response, 400, { ok: false, error: problem });

  const job = {
    code: payload.code,
    functionName: payload.function_name,
    tests: payload.tests,
    timeLimitMs: Number(payload.time_limit_ms) || 2000,
    memoryLimitMb: Number(payload.memory_limit_mb) || 128,
  };

  const started = Date.now();
  try {
    const report =
      payload.language === "javascript"
        ? runJavaScript(job)
        : await runPython(job, PYTHON_BIN);
    report.runtime_ms = report.runtime_ms || Date.now() - started;
    return json(response, 200, report);
  } catch (error) {
    console.error("[runner] execution failed:", error);
    return json(response, 500, { ok: false, error: `The runner crashed: ${error.message}`, results: [] });
  }
});

server.listen(PORT, HOST, () => {
  console.log(`[runner] listening on http://${HOST}:${PORT}/run`);
  console.log(`[runner] javascript: node:vm (timeout + no require/process/fetch)`);
  probePython().then((status) => {
    Object.assign(pythonHealth, status);
    const line = status.available
      ? `python:     ${status.version} via ${PYTHON_BIN} (subprocess -I -S, AST allowlist)`
      : `python:     UNAVAILABLE — ${status.error}`;
    console.log(`[runner] ${line}`);
    console.log(`[runner] NOT production-hardened. See README.md before exposing this beyond localhost.`);
  });
});

/**
 * The Windows `python` command is often a Store alias that starts nothing, so a
 * broken PYTHON_BIN must be reported at boot instead of surfacing as a timeout.
 */
function probePython() {
  return new Promise((resolve) => {
    const child = spawn(PYTHON_BIN, ["-I", "-S", "-c", "import sys; print(sys.version.split()[0])"], {
      env: minimalEnv(),
      windowsHide: true,
    });
    let out = "";
    let done = false;
    const settle = (result) => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      child.kill();
      resolve(result);
    };
    const timer = setTimeout(() => settle({ available: false, error: `${PYTHON_BIN} did not answer within 8s.` }), 8000);
    child.stdout.on("data", (chunk) => (out += chunk.toString()));
    child.on("error", (error) =>
      settle({ available: false, error: `${PYTHON_BIN} could not start (${error.code || error.message}).` })
    );
    child.on("close", (code) =>
      settle(
        code === 0 && out.trim()
          ? { available: true, version: out.trim().split(/\r?\n/)[0] }
          : { available: false, error: `${PYTHON_BIN} exited with code ${code}.` }
      )
    );
  });
}

function validate(payload) {
  if (typeof payload.code !== "string" || !payload.code.trim()) return "No code was supplied.";
  if (Buffer.byteLength(payload.code, "utf8") > MAX_CODE_BYTES) {
    return `Your submission is larger than the ${MAX_CODE_BYTES} byte limit.`;
  }
  if (!ALLOWED_LANGUAGES.has(payload.language)) {
    return `Unsupported language "${payload.language}". Supported: ${[...ALLOWED_LANGUAGES].join(", ")}.`;
  }
  if (typeof payload.function_name !== "string" || !IDENTIFIER.test(payload.function_name)) {
    return "The function name is not a valid identifier.";
  }
  if (!Array.isArray(payload.tests) || payload.tests.length === 0) return "No test cases were supplied.";
  if (payload.tests.length > 40) return "Too many test cases for one run.";
  for (const test of payload.tests) {
    if (!test || typeof test !== "object") return "A test case is malformed.";
    if (!Array.isArray(test.args)) return "A test case is missing its arguments array.";
    if (test.args.length > 10) return "A test case passes too many arguments.";
  }
  return "";
}

function readBody(request) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    request.on("data", (chunk) => {
      size += chunk.length;
      if (size > MAX_BODY_BYTES) {
        reject(Object.assign(new Error("Request body too large."), { statusCode: 413 }));
        request.destroy();
        return;
      }
      chunks.push(chunk);
    });
    request.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    request.on("error", reject);
  });
}

function header(request, name) {
  const value = request.headers[name];
  return typeof value === "string" ? value : "";
}

function timingSafeEquals(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let index = 0; index < a.length; index += 1) diff |= a.charCodeAt(index) ^ b.charCodeAt(index);
  return diff === 0;
}

function json(response, status, body) {
  const text = JSON.stringify(body);
  response.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(text),
    "Cache-Control": "no-store",
  });
  response.end(text);
}

/** Minimal KEY=value loader so the runner needs no extra dependency. */
function loadDotEnv(file) {
  let text;
  try {
    text = fs.readFileSync(file, "utf8");
  } catch {
    return;
  }
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const index = trimmed.indexOf("=");
    if (index === -1) continue;
    const key = trimmed.slice(0, index).trim();
    if (process.env[key] !== undefined) continue;
    process.env[key] = trimmed.slice(index + 1).trim().replace(/^["']|["']$/g, "");
  }
}
