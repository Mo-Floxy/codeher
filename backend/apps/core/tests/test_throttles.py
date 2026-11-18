"""Throttle wiring invariants, both directions.

A scope with a rate in settings but no view is a limit that everyone believes in:
`sandbox` sat unused there while `run/` and `submit/` graded without a ceiling.
A scope used by a view but absent from settings is an `ImproperlyConfigured` 500 on
the first request to it. Neither shows up in a deploy log, so both are asserted here.
"""

import ast

from django.conf import settings

from apps.core.tests.test_permissions import app_source_files


def string_assigned_in_class_body(node, attribute):
    for statement in node.body:
        if not isinstance(statement, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == attribute for t in statement.targets):
            continue
        value = statement.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            yield value.value


def is_throttle_class(node):
    return any(isinstance(base, ast.Name) and base.id.endswith("Throttle") for base in node.bases)


def scopes_used():
    """`throttle_scope` on any view class, plus `scope` on any throttle class.

    Only class bodies are read: a local `scope` variable inside a handler is a query
    parameter, not a rate-limit scope, and conflating the two would make this test
    pass or fail on unrelated renames.
    """
    used = set()
    for module in app_source_files():
        tree = ast.parse(module.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            used.update(string_assigned_in_class_body(node, "throttle_scope"))
            if is_throttle_class(node):
                used.update(string_assigned_in_class_body(node, "scope"))
    return used


def configured_scopes():
    return set(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"])


def test_every_configured_rate_is_referenced_somewhere():
    unused = configured_scopes() - scopes_used()
    assert not unused, (
        f"{sorted(unused)} have a rate in settings but no view names them, so nothing is "
        "actually limited. Wire the scope to the endpoint, or drop the rate."
    )


def test_every_scope_a_view_names_has_a_configured_rate():
    missing = scopes_used() - configured_scopes()
    assert not missing, (
        f"{sorted(missing)} are used by a view with no entry in DEFAULT_THROTTLE_RATES; "
        "the first request to those endpoints raises ImproperlyConfigured."
    )
