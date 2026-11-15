/**
 * Python execution: one subprocess per request, nothing inherited.
 *
 * The submission is validated by an AST allowlist inside the harness before it
 * is compiled, the interpreter starts with `-I -S` (isolated, no site-packages),
 * the environment is reduced to what the launcher itself needs, and the process
 * is killed if it overruns its time budget.
 */

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawn } = require("node:child_process");

const HARNESS = path.join(__dirname, "python_harness.py");

// Python needs these on Windows to start at all; nothing else is forwarded.
const PASSTHROUGH = ["SystemRoot", "WINDIR", "COMSPEC", "TEMP", "TMP", "PATH", "LANG", "LC_ALL"];

function minimalEnv() {
  const env = {};
  for (const key of PASSTHROUGH) {
    if (process.env[key] !== undefined) env[key] = process.env[key];
  }
  return env;
}

function runPython({ code, functionName, tests, timeLimitMs, memoryLimitMb }, pythonBin) {
  const budgetMs = Math.min(60000, Math.max(1000, timeLimitMs || 2000) * Math.max(1, (tests || []).length) + 2000);

  let dir;
  try {
    dir = fs.mkdtempSync(path.join(os.tmpdir(), "codeher-runner-"));
  } catch (error) {
    return Promise.resolve(unavailable(`The runner could not create a work directory: ${error.message}`));
  }

  const jobPath = path.join(dir, "job.json");
  const outPath = path.join(dir, "result.json");

  try {
    fs.writeFileSync(jobPath, JSON.stringify({ code, function_name: functionName, tests, memory_limit_mb: memoryLimitMb }));
  } catch (error) {
    cleanup(dir);
    return Promise.resolve(unavailable(`The runner could not stage the submission: ${error.message}`));
  }

  return new Promise((resolve) => {
    let settled = false;
    const finish = (payload) => {
      if (settled) return;
      settled = true;
      cleanup(dir);
      resolve(payload);
    };

    const child = spawn(pythonBin || "python", ["-I", "-S", HARNESS, jobPath, outPath], {
      env: minimalEnv(),
      cwd: dir,
      windowsHide: true,
      stdio: ["ignore", "pipe", "pipe"],
    });

    let stderr = "";
    child.stderr.on("data", (chunk) => {
      stderr = (stderr + chunk.toString()).slice(-4000);
    });

    const killer = setTimeout(() => {
      child.kill("SIGKILL");
      finish({
        ok: false,
        error: `Your code ran longer than the ${Math.round(budgetMs / 1000)}s budget and was stopped.`,
        runtime_ms: budgetMs,
        results: (tests || []).map((test) => ({
          name: test.name,
          passed: false,
          expected: test.expected,
          actual: null,
          error: "Timed out.",
        })),
      });
    }, budgetMs);

    child.on("error", (error) => {
      clearTimeout(killer);
      const message =
        error.code === "ENOENT"
          ? `The Python interpreter "${pythonBin || "python"}" was not found. Set PYTHON_BIN when starting the runner.`
          : `Could not start the Python sandbox: ${error.message}`;
      finish(unavailable(message));
    });

    child.on("close", (exitCode) => {
      clearTimeout(killer);
      let report;
      try {
        report = JSON.parse(fs.readFileSync(outPath, "utf8"));
      } catch {
        finish(
          unavailable(
            `The Python sandbox stopped before it could report (exit ${exitCode}). ` +
              (stderr ? `Interpreter said: ${stderr.slice(0, 300)}` : "")
          )
        );
        return;
      }
      const passed = (report.results || []).filter((result) => result.passed).length;
      finish({ ...report, ok: Boolean(report.error) === false && passed === (report.results || []).length });
    });
  });
}

function unavailable(message) {
  return { ok: false, error: message, runtime_ms: 0, results: [] };
}

function cleanup(dir) {
  try {
    fs.rmSync(dir, { recursive: true, force: true });
  } catch {
    // A leftover temp directory is not worth failing a submission over.
  }
}

module.exports = { runPython, minimalEnv };
