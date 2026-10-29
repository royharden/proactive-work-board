"""Named source fault controls for later authorized execution; never enabled by default."""
class PrecommitAbort(RuntimeError):
    """Injected before COMMIT: the surrounding transaction must roll back."""


class PostcommitAckLoss(RuntimeError):
    """Injected after COMMIT: callers recover via lookup_intent, never reapply."""
