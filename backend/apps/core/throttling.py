"""Rate limits that name what they protect.

`ScopedRateThrottle` needs a `throttle_scope` on the view, and a viewset whose
expensive work sits in `@action` methods cannot state one per action without
making the catalogue unbrowseable. A class with its own `scope` travels with the
endpoints that need it; a scope missing from `REST_FRAMEWORK` then fails on the
first request instead of silently not limiting anything.
"""

from rest_framework.throttling import SimpleRateThrottle


class SandboxThrottle(SimpleRateThrottle):
    """Calls that make the runner start a real process.

    Keyed by account, because the free-tier runner has no capacity to share
    between browser tabs: one learner hammering `run/` starves everyone else.
    Anonymous traffic — which cannot grade anything, since both endpoints need a
    token — falls back to its IP, as `SimpleRateThrottle.get_ident` does.
    """

    scope = "sandbox"

    # `SimpleRateThrottle` is the abstract half of the pair; `ScopedRateThrottle`
    # supplies the key but overwrites `scope` from the view on every request, which
    # is the one thing a fixed-scope throttle must not do.
    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}
