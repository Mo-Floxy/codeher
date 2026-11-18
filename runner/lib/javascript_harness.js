/**
 * Child entry for one JavaScript submission.
 *
 * Spawned by runJavaScriptIsolated with a stripped environment and, where the
 * runtime supports it, Node's permission model. The job arrives on stdin and the
 * report leaves on stdout, so this process never needs to write a file: a
 * submission that breaks out of the vm realm still lands in a short-lived process
 * that was never given the database password, the JWT signing key or the runner's
 * shared secret, and cannot spawn anything else.
 */

const { runJavaScript } = require("./javascript");

let text = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => (text += chunk));
process.stdin.on("error", () => process.exit(1));
process.stdin.on("end", () => {
  let report;
  try {
    const job = JSON.parse(text);
    report = runJavaScript({
      code: job.code,
      functionName: job.function_name,
      tests: job.tests,
      timeLimitMs: job.time_limit_ms,
    });
  } catch (error) {
    report = { ok: false, error: `The JavaScript sandbox failed: ${error.message}`, runtime_ms: 0, results: [] };
  }
  process.stdout.write(JSON.stringify(report));
});
