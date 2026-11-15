"""Trusted harness executed as a subprocess for one Python submission.

Usage:  python -I -S python_harness.py <job.json> <result.json>

The learner's source is parsed and every AST node must appear in the allowlist,
imports, `with`, `global`, `async` and any attribute or name beginning with an
underscore are rejected before a single line is compiled. Execution then happens
against a restricted `__builtins__` mapping, and the process is started with
`-I -S` and a stripped environment so nothing is inherited from the runner.
"""

import ast
import json
import re
import sys
import time

DUNDER_RE = re.compile(r"__\w+__")

ALLOWED_NODE_NAMES = [
    "Module", "FunctionDef", "ClassDef", "Return",
    "Assign", "AugAssign", "AnnAssign", "Delete",
    "For", "While", "If", "Expr", "Pass", "Break", "Continue", "Raise", "Try", "TryStar",
    "BoolOp", "BinOp", "UnaryOp", "Lambda", "IfExp", "Compare", "Call",
    "FormattedValue", "JoinedStr", "Constant", "Attribute", "Subscript", "Starred", "Slice",
    "Name", "List", "Tuple", "Set", "Dict",
    "ListComp", "SetComp", "DictComp", "GeneratorExp", "comprehension",
    "arguments", "arg", "keyword",
    "Match", "MatchValue", "MatchSingleton", "MatchSequence", "MatchMapping",
    "MatchClass", "MatchStar", "MatchAs", "MatchOr", "pattern", "case",
    "Add", "Sub", "Mult", "MatMult", "Div", "Mod", "Pow", "LShift", "RShift",
    "BitOr", "BitXor", "BitAnd", "FloorDiv",
    "Invert", "Not", "UAdd", "USub", "And", "Or",
    "Eq", "NotEq", "Lt", "LtE", "Gt", "GtE", "Is", "IsNot", "In", "NotIn",
    "Load", "Store", "Del",
]
# Deliberately absent: Import, ImportFrom, With, AsyncWith, Global, Nonlocal,
# Await, AsyncFor and every async function form.
FORBIDDEN_NODES = {
    getattr(ast, name)
    for name in ("Import", "ImportFrom", "With", "AsyncWith", "Global", "Nonlocal", "Await")
    if hasattr(ast, name)
}
ALLOWED_NODES = {getattr(ast, name) for name in ALLOWED_NODE_NAMES if hasattr(ast, name)}

BANNED_NAMES = {
    "__import__", "open", "exec", "eval", "compile", "globals", "locals", "vars", "dir",
    "input", "breakpoint", "exit", "quit", "memoryview", "getattr", "setattr", "delattr",
    "help", "type", "object", "__builtins__", "__loader__", "__spec__", "__name__",
    "__file__", "__debug__", "id", "super",
}

SAFE_BUILTINS = {
    "abs": abs, "all": all, "any": any, "bin": bin, "bool": bool, "bytes": bytes,
    "chr": chr, "complex": complex, "dict": dict, "divmod": divmod, "enumerate": enumerate,
    "filter": filter, "float": float, "format": format, "frozenset": frozenset, "hex": hex,
    "int": int, "isinstance": isinstance, "issubclass": issubclass, "len": len, "list": list,
    "map": map, "max": max, "min": min, "oct": oct, "ord": ord, "pow": pow,
    "print": lambda *a, **k: None,
    "property": property, "range": range, "repr": repr, "reversed": reversed, "round": round,
    "set": set, "slice": slice, "sorted": sorted, "staticmethod": staticmethod,
    "classmethod": classmethod, "str": str, "sum": sum, "tuple": tuple, "zip": zip,
    "ArithmeticError": ArithmeticError, "AssertionError": AssertionError, "AttributeError": AttributeError,
    "Exception": Exception, "IndexError": IndexError, "KeyError": KeyError, "LookupError": LookupError,
    "NameError": NameError, "RuntimeError": RuntimeError, "StopIteration": StopIteration,
    "TypeError": TypeError, "ValueError": ValueError, "ZeroDivisionError": ZeroDivisionError,
}


class UnsafeCode(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def validate(source):
    try:
        tree = ast.parse(source, filename="submission.py", mode="exec")
    except SyntaxError as error:
        raise UnsafeCode(f"Syntax error on line {error.lineno}: {error.msg}") from error

    for node in ast.walk(tree):
        if type(node) in FORBIDDEN_NODES:
            raise UnsafeCode(f"{type(node).__name__} statements are not allowed in the sandbox.")
        if type(node) not in ALLOWED_NODES:
            raise UnsafeCode(f"{type(node).__name__} is not allowed in the sandbox.")
        if isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            raise UnsafeCode(f"`{node.id}` is not available in the sandbox.")
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            raise UnsafeCode("Private and dunder attributes are not reachable in the sandbox.")
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if DUNDER_RE.fullmatch(node.value):
                raise UnsafeCode("Dunder attribute names are not reachable through strings here.")
    return tree


def execute(tree, source, function_name, tests):
    namespace = {"__builtins__": SAFE_BUILTINS, "__name__": "submission"}
    compiled = compile(tree, filename="submission.py", mode="exec")
    started = time.perf_counter()
    exec(compiled, namespace)  # noqa: S102 - source already passed the AST allowlist
    function = namespace.get(function_name)
    if not callable(function):
        raise UnsafeCode(f"No function named `{function_name}` was defined.")

    results = []
    for test in tests:
        entry = {
            "name": test.get("name", "test"),
            "passed": False,
            "expected": display(test.get("expected")),
            "actual": None,
            "error": "",
        }
        try:
            actual = function(*test.get("args", []))
            entry["actual"] = display(actual)
            entry["passed"] = equal(actual, test.get("expected"))
        except UnsafeCode as error:
            entry["error"] = error.message
        except Exception as error:  # reported to the learner, never swallowed
            entry["error"] = f"{type(error).__name__}: {error}".split("\n")[0][:400]
        results.append(entry)

    elapsed = int((time.perf_counter() - started) * 1000)
    return results, elapsed


def equal(actual, expected):
    if isinstance(actual, bool) != isinstance(expected, bool):
        return False
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return actual == expected
    if isinstance(actual, list) and isinstance(expected, list):
        return len(actual) == len(expected) and all(equal(a, b) for a, b in zip(actual, expected))
    if isinstance(actual, dict) and isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(equal(actual[k], expected[k]) for k in actual)
    return actual == expected


def display(value):
    try:
        text = json.dumps(value)
    except (TypeError, ValueError):
        text = json.dumps(repr(value))
    if len(text) > 800:
        return f"{text[:800]}…"
    return json.loads(text) if len(text) <= 800 else text


def main():
    job_path, out_path = sys.argv[1], sys.argv[2]
    with open(job_path, "r", encoding="utf-8") as handle:
        job = json.load(handle)

    payload = {"ok": False, "error": "", "runtime_ms": 0, "results": []}
    try:
        tree = validate(job.get("code", ""))
        results, elapsed = execute(tree, job.get("code", ""), job.get("function_name") or "solution",
                                   job.get("tests", []))
        payload.update({"results": results, "runtime_ms": elapsed,
                        "ok": bool(results) and all(result["passed"] for result in results)})
    except UnsafeCode as error:
        payload["error"] = error.message
        payload["results"] = [
            {"name": test.get("name", "test"), "passed": False, "expected": display(test.get("expected")),
             "actual": None, "error": error.message}
            for test in job.get("tests", [])
        ]
    except RecursionError:
        payload["error"] = "Your function recursed too deeply. Add a base case that stops."
    except MemoryError:
        payload["error"] = "The solution used too much memory."

    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)


if __name__ == "__main__":
    sys.setrecursionlimit(3000)
    main()
