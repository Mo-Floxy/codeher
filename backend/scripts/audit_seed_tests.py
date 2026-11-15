"""Audit every seeded challenge by running a reference solution in the real sandbox.

A wrong `expected` in the seed is invisible until a learner writes correct code and
fails, so this script grades each challenge against a known-good JavaScript
implementation and reports any case whose expectation disagrees.

    .venv\\Scripts\\python.exe scripts\\audit_seed_tests.py

Needs the runner service up (see codeher/runner/README.md) and RUNNER_SHARED_SECRET
in runner/.env.
"""

import json
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apps.core.seed.challenges_seed import CHALLENGES  # noqa: E402

RUNNER_DIR = Path(__file__).resolve().parents[2] / "runner"

REFERENCE = {
    "Reverse a String": "function solution(text){return String(text).split('').reverse().join('');}",
    "Sum an Array": "function solution(numbers){return numbers.reduce((total, n) => total + n, 0);}",
    "Largest Number": "function solution(numbers){return Math.max(...numbers);}",
    "Count the Vowels": "function solution(text){let n=0;for(const c of text){if('aeiou'.includes(c))n++;}return n;}",
    "Running Total": "function solution(numbers){let t=0;return numbers.map(n=>(t+=n));}",
    "Palindrome Check": "function solution(text){return text===text.split('').reverse().join('');}",
    "Remove Duplicates": "function solution(values){const out=[];for(const v of values){if(!out.includes(v))out.push(v);}return out;}",
    "Two Sum Indices": (
        "function solution(numbers,target){for(let i=0;i<numbers.length;i++)"
        "for(let j=i+1;j<numbers.length;j++)if(numbers[i]+numbers[j]===target)return [i,j];return [];}"
    ),
    "Valid Parentheses": (
        "function solution(text){const pairs={'(' : ')', '[': ']', '{': '}'};const stack=[];"
        "for(const c of text){if(pairs[c])stack.push(c);"
        "else{const open=stack.pop();if(!open||pairs[open]!==c)return false;}}return stack.length===0;}"
    ),
    "Title Case": (
        "function solution(sentence){return sentence.split(' ').map(w=>w.charAt(0).toUpperCase()"
        "+w.slice(1).toLowerCase()).join(' ');}"
    ),
    "FizzBuzz List": (
        "function solution(n){const out=[];for(let i=1;i<=n;i++){"
        "out.push(i%15===0?'FizzBuzz':i%3===0?'Fizz':i%5===0?'Buzz':String(i));}return out;}"
    ),
    "Flatten One Level": "function solution(nested){const out=[];for(const item of nested){if(Array.isArray(item))out.push(...item);else out.push(item);}return out;}",
}


def runner_settings():
    env = {}
    path = RUNNER_DIR / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def main():
    settings = runner_settings()
    base = f"http://127.0.0.1:{os.environ.get('RUNNER_PORT') or settings.get('RUNNER_PORT') or 8090}"
    # Same precedence the two services use: real environment, then runner/.env,
    # then the documented development default.
    secret = os.environ.get("RUNNER_SHARED_SECRET") or settings.get("RUNNER_SHARED_SECRET") or "dev-runner-secret"

    failures = 0
    for challenge in CHALLENGES:
        code = REFERENCE.get(challenge["title"])
        if code is None:
            print(f"SKIP  {challenge['title']} — no reference solution written")
            continue
        payload = {
            "language": "javascript",
            "code": code,
            "function_name": "solution",
            "time_limit_ms": 2000,
            "memory_limit_mb": 128,
            "tests": [{"name": t["name"], "args": t["args"], "expected": t["expected"]} for t in challenge["tests"]],
        }
        response = requests.post(
            f"{base}/run",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json", "X-Runner-Secret": secret},
            timeout=60,
        )
        if response.status_code != 200:
            print(f"ERROR {challenge['title']} — runner said {response.status_code}: {response.text[:200]}")
            failures += 1
            continue
        report = response.json()
        for test, result in zip(challenge["tests"], report["results"]):
            if not result["passed"]:
                failures += 1
                kind = "public" if test.get("public") else "hidden"
                print(
                    f"WRONG {challenge['title']} / {test['name']} ({kind})\n"
                    f"      args={json.dumps(test['args'])} expected={json.dumps(test['expected'])} "
                    f"reference_returned={json.dumps(result.get('actual'))}"
                )
        status = "ok" if all(r["passed"] for r in report["results"]) else "see above"
        print(f"      {challenge['title']}: {len(report['results'])} cases, {status}")

    print(f"\n{failures} mismatching expectation(s) across {len(CHALLENGES)} challenges.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
