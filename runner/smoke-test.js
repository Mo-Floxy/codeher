/**
 * End-to-end smoke test for the runner. The runner must be listening already:
 *
 *   npm start          # in one terminal
 *   npm run smoke      # in another
 *
 * It exercises the secret check, both languages, the sandbox escapes that must
 * be blocked, and the infinite-loop timeout.
 */

const http = require("node:http");

const PORT = Number(process.env.RUNNER_PORT || 8090);
const SECRET = process.env.RUNNER_SHARED_SECRET || "dev-runner-secret";
const BASE = { host: "127.0.0.1", port: PORT, path: "/run", method: "POST" };

let failures = 0;

function post(payload, secret = SECRET) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(payload);
    const request = http.request(
      { ...BASE, headers: { "Content-Type": "application/json", "X-Runner-Secret": secret, "Content-Length": Buffer.byteLength(body) } },
      (response) => {
        let text = "";
        response.on("data", (chunk) => (text += chunk));
        response.on("end", () => resolve({ status: response.statusCode, body: safeJson(text) }));
      }
    );
    request.on("error", reject);
    request.end(body);
  });
}

function safeJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return { raw: text };
  }
}

function check(label, condition, detail) {
  if (condition) {
    console.log(`  pass  ${label}`);
  } else {
    failures += 1;
    console.log(`  FAIL  ${label}${detail ? ` — ${JSON.stringify(detail).slice(0, 240)}` : ""}`);
  }
}

async function main() {
  console.log(`Runner smoke test against http://127.0.0.1:${PORT}\n`);

  const noSecret = await post({ language: "javascript", code: "function solution(){return 1}", function_name: "solution", tests: [{ name: "a", args: [], expected: 1 }] }, "wrong-secret");
  check("rejects a bad shared secret with 401", noSecret.status === 401, noSecret);

  const js = await post({
    language: "javascript",
    function_name: "solution",
    time_limit_ms: 2000,
    code: "function solution(text) { return text.split('').reverse().join(''); }",
    tests: [
      { name: "hello", args: ["hello"], expected: "olleh" },
      { name: "empty", args: [""], expected: "" },
      { name: "wrong on purpose", args: ["a"], expected: "b" },
    ],
  });
  check("javascript passes the correct cases", js.body.results?.[0]?.passed === true && js.body.results?.[1]?.passed === true, js.body);
  check("javascript reports a failing case", js.body.results?.[2]?.passed === false, js.body.results?.[2]);
  check("javascript run is not marked ok", js.body.ok === false, js.body);

  const arrow = await post({
    language: "javascript",
    function_name: "solution",
    code: "const solution = (n) => n * 2;",
    tests: [{ name: "double", args: [21], expected: 42 }],
  });
  check("javascript accepts an arrow-function answer", arrow.body.results?.[0]?.passed === true, arrow.body);

  // Arrays and objects are built inside the sandbox realm, so their prototypes are
  // not the ones compare.js can see. A realm-sensitive equality check silently fails
  // every array-returning challenge, which is exactly what happened once.
  const arrays = await post({
    language: "javascript",
    function_name: "solution",
    code: "function solution(n){const out=[];for(let i=1;i<=n;i++)out.push(String(i));return out;}",
    tests: [
      { name: "list of strings", args: [3], expected: ["1", "2", "3"] },
      { name: "wrong length must fail", args: [3], expected: ["1", "2"] },
    ],
  });
  check(
    "javascript array answers compare equal across realms",
    arrays.body.results?.[0]?.passed === true && arrays.body.results?.[1]?.passed === false,
    arrays.body
  );

  const objects = await post({
    language: "javascript",
    function_name: "solution",
    code: "function solution(){return {ok: true, count: 2};}",
    tests: [
      { name: "plain object", args: [], expected: { ok: true, count: 2 } },
      { name: "different value", args: [], expected: { ok: true, count: 3 } },
    ],
  });
  check(
    "javascript object answers compare equal across realms",
    objects.body.results?.[0]?.passed === true && objects.body.results?.[1]?.passed === false,
    objects.body
  );

  const boolVsNumber = await post({
    language: "javascript",
    function_name: "solution",
    code: "function solution(){return true;}",
    tests: [{ name: "true is not 1", args: [], expected: 1 }],
  });
  check("javascript keeps booleans and numbers apart", boolVsNumber.body.results?.[0]?.passed === false, boolVsNumber.body);

  const escaped = await post({
    language: "javascript",
    function_name: "solution",
    code: 'function solution() { return require("fs").readFileSync("C:/Windows/win.ini", "utf8"); }',
    tests: [{ name: "read file", args: [], expected: "" }],
  });
  check("javascript cannot require() the filesystem", /not defined/.test(escaped.body.results?.[0]?.error || ""), escaped.body);

  // Anything the runner *assigns* into the sandbox arrives with its host realm
  // attached. Injecting Object/JSON/Array, a console stub, or the test arguments
  // therefore gave a submission a host `Function` constructor — one call from
  // `process`, whose environment holds the database password and JWT signing key.
  // Every one of these must now answer `undefined` or `contained`.
  const hostBuiltins = await post({
    language: "javascript",
    function_name: "solution",
    code: 'function solution(){ return String(Object.constructor("return typeof process")()) + "/" + String(Array.constructor("return typeof require")()); }',
    tests: [{ name: "injected built-ins", args: [], expected: "undefined/undefined" }],
  });
  check("javascript built-ins belong to the sandbox realm", hostBuiltins.body.results?.[0]?.passed === true, hostBuiltins.body);

  const hostArguments = await post({
    language: "javascript",
    function_name: "solution",
    code: 'function solution(a){ try { return String(a.constructor.constructor("return typeof process")()); } catch (e) { return "contained"; } }',
    tests: [{ name: "argument realm", args: [1], expected: "undefined" }],
  });
  check("test arguments belong to the sandbox realm", hostArguments.body.results?.[0]?.passed === true, hostArguments.body);

  const hostConsole = await post({
    language: "javascript",
    function_name: "solution",
    code: 'function solution(){ try { console.log("x"); return String(console.constructor.constructor("return typeof process")()); } catch (e) { return "contained"; } }',
    tests: [{ name: "console realm", args: [], expected: "undefined" }],
  });
  check("the console stub belongs to the sandbox realm", hostConsole.body.results?.[0]?.passed === true, hostConsole.body);

  const childProcess = await post({
    language: "javascript",
    function_name: "solution",
    code: 'function solution(){ try { Object.constructor("return process")().mainModule.require("child_process").execSync("echo pwned"); return "ESCAPED"; } catch (e) { return "contained"; } }',
    tests: [{ name: "no shell", args: [], expected: "contained" }],
  });
  check("javascript cannot spawn a process", childProcess.body.results?.[0]?.passed === true, childProcess.body);

  const leakedEnv = await post({
    language: "javascript",
    function_name: "solution",
    code:
      'function solution(){ try { const env = Object.constructor("return process")().env; ' +
      'return ["RUNNER_SHARED_SECRET","MYSQL_PASSWORD","DJANGO_SECRET_KEY","JWT_SIGNING_KEY"].some((k) => k in env) ? "LEAKED" : "no-credentials"; ' +
      "} catch (e) { return \"no-credentials\"; } }",
    tests: [{ name: "no credentials in env", args: [], expected: "no-credentials" }],
  });
  check("javascript cannot read runner credentials", leakedEnv.body.results?.[0]?.passed === true, leakedEnv.body);

  const loop = await post({
    language: "javascript",
    function_name: "solution",
    time_limit_ms: 700,
    code: "function solution() { while (true) {} }",
    tests: [{ name: "hangs", args: [], expected: 1 }],
  });
  check("javascript infinite loop is stopped, not fatal", loop.body.results?.[0]?.passed === false, loop.body);

  const py = await post({
    language: "python",
    function_name: "solution",
    time_limit_ms: 3000,
    code: "def solution(text):\n    return text[::-1]\n",
    tests: [
      { name: "hello", args: ["hello"], expected: "olleh" },
      { name: "empty", args: [""], expected: "" },
    ],
  });
  check("python passes both cases", py.body.ok === true && py.body.results?.length === 2, py.body);

  const pyImport = await post({
    language: "python",
    function_name: "solution",
    code: 'import os\n\ndef solution(x):\n    return os.getcwd()\n',
    tests: [{ name: "import", args: [], expected: "" }],
  });
  check("python blocks import statements", /Import/.test(pyImport.body.error || ""), pyImport.body);

  const pyOpen = await post({
    language: "python",
    function_name: "solution",
    code: 'def solution(x):\n    return open("C:/Windows/win.ini").read()\n',
    tests: [{ name: "open", args: [], expected: "" }],
  });
  check("python blocks open()", /open/.test(pyOpen.body.error || ""), pyOpen.body);

  const pyDunder = await post({
    language: "python",
    function_name: "solution",
    code: "def solution(x):\n    return x.__class__.__mro__\n",
    tests: [{ name: "dunder", args: [1], expected: "" }],
  });
  check("python blocks dunder attribute access", /[Pp]rivate|dunder/.test(pyDunder.body.error || ""), pyDunder.body);

  // `Try` was allowlisted but `ExceptHandler` — the node type of each `except`
  // clause — was not, so every submission that caught an exception was rejected as
  // unsafe. A learner writing ordinary defensive Python was told their code was a
  // threat.
  const pyTry = await post({
    language: "python",
    function_name: "solution",
    code:
      "def solution(n):\n" +
      "    try:\n" +
      "        return 10 // n\n" +
      "    except ZeroDivisionError:\n" +
      "        return -1\n",
    tests: [
      { name: "divides", args: [2], expected: 5 },
      { name: "caught", args: [0], expected: -1 },
    ],
  });
  check("python allows try/except", pyTry.body.ok === true, pyTry.body);

  const pyLoop = await post({
    language: "python",
    function_name: "solution",
    time_limit_ms: 1000,
    code: "def solution(x):\n    while True:\n        pass\n",
    tests: [{ name: "hangs", args: [], expected: 1 }],
  });
  check("python infinite loop is killed", pyLoop.body.results?.[0]?.passed === false, pyLoop.body);

  const badLanguage = await post({ language: "ruby", code: "def solution; 1; end", function_name: "solution", tests: [] });
  check("unknown language is rejected with 400", badLanguage.status === 400, badLanguage.body);

  const noTests = await post({ language: "javascript", code: "function solution(){}", function_name: "solution", tests: [] });
  check("empty test list is rejected with 400", noTests.status === 400, noTests.body);

  console.log(failures ? `\n${failures} check(s) failed.` : "\nAll runner checks passed.");
  process.exit(failures ? 1 : 0);
}

main().catch((error) => {
  console.error(`Runner is not reachable at http://127.0.0.1:${PORT}: ${error.message}`);
  console.error("Start it first with `npm start`.");
  process.exit(1);
});
