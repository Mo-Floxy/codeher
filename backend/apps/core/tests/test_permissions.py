"""Static permission invariants for the whole API.

`DEFAULT_PERMISSION_CLASSES` is `AllowAny`, so a view class that forgets to state its
own gate is public — in production, with no test failing and nothing in a deploy log to
indicate it. All 67 view classes here state a gate today, so this is not a description of
a known hole; it is the tripwire that keeps the next endpoint from becoming one, and the
reason the public endpoints are named rather than assumed.
"""

import ast
import pathlib

WRITE_METHODS = {"post", "put", "patch", "delete", "create", "update", "partial_update", "destroy"}

# Endpoints that must answer without a token, because obtaining one is the point.
PUBLIC_BY_DESIGN = {"RegisterView", "LoginView", "ForgotPasswordView", "ResetPasswordView"}

DRF_BASES = {
    "APIView",
    "ViewSet",
    "GenericViewSet",
    "ModelViewSet",
    "ReadOnlyModelViewSet",
    "GenericAPIView",
    "ListAPIView",
    "RetrieveAPIView",
    "CreateAPIView",
    "UpdateAPIView",
    "DestroyAPIView",
}

def app_source_files():
    """Every source file of every installed app, so a new app is covered automatically.

    Walking INSTALLED_APPS rather than a hardcoded directory depth is what keeps this
    honest: the first draft of this test quietly scanned nothing and still passed, which
    is exactly the shape of failure a permission tripwire must not be able to have.
    """
    from django.apps import apps

    for config in apps.get_app_configs():
        if not config.name.startswith("apps."):
            continue
        directory = pathlib.Path(config.path)
        for module in sorted(directory.glob("*.py")):
            if module.name in {"tests.py"} or "migrations" in module.parts:
                continue
            yield module


def view_classes():
    """Every class that is (perhaps through a local parent) a DRF entry point."""
    for module in app_source_files():
        tree = ast.parse(module.read_text(encoding="utf-8"))
        classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
        label = f"{module.parent.name}/{module.name}"
        for name, node in classes.items():
            if is_drf_view(node, classes):
                yield label, name, node, classes


def is_drf_view(node, classes, seen=()):
    if node.name in seen:
        return False
    for base in node.bases:
        if not isinstance(base, ast.Name):
            continue
        if base.id in DRF_BASES:
            return True
        if base.id in classes and is_drf_view(classes[base.id], classes, seen + (node.name,)):
            return True
    return False


def states_gate(node, classes):
    body = ast.dump(node)
    if "permission_classes" in body or "get_permissions" in body:
        return True
    return any(
        isinstance(base, ast.Name) and base.id in classes and states_gate(classes[base.id], classes)
        for base in node.bases
    )


def declares_allow_any(node):
    for statement in node.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "permission_classes" for target in statement.targets
        ):
            return "AllowAny" in ast.dump(statement.value)
    return False


def has_write_entry_points(node):
    for member in node.body:
        if not isinstance(member, ast.FunctionDef):
            continue
        if member.name.lower() in WRITE_METHODS:
            return True
        if any(isinstance(dec, ast.Name) and dec.id == "action" for dec in member.decorator_list):
            return True
    return False


def test_every_drf_view_states_its_own_permission_gate():
    ungated = [f"{label}::{name}" for label, name, node, classes in view_classes() if not states_gate(node, classes)]
    assert not ungated, (
        "These views inherit AllowAny from settings instead of declaring a gate: " + ", ".join(ungated)
    )


def test_allow_any_views_that_can_write_gate_their_writes():
    offenders = [
        f"{label}::{name}"
        for label, name, node, classes in view_classes()
        if declares_allow_any(node) and name not in PUBLIC_BY_DESIGN and has_write_entry_points(node)
        and "get_permissions" not in ast.dump(node)
    ]
    assert not offenders, (
        f"{offenders} accept writes with no token. Gate them in get_permissions, or add the "
        "class to PUBLIC_BY_DESIGN if anonymous writes are really intended."
    )


def test_the_permission_scan_is_not_silently_scanning_nothing():
    total = list(view_classes())
    assert len(total) > 40, f"only {len(total)} view classes found - the scan itself is broken"
