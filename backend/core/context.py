"""
core/context.py — Global singleton storage for InferenceContext.
Set once during FastAPI lifespan startup; read on every request.
"""

_CTX = None


def set_context(ctx) -> None:
    """Called once from main.py lifespan at startup."""
    global _CTX
    _CTX = ctx


def get_context():
    """Called by API route handlers to retrieve the loaded context."""
    if _CTX is None:
        raise RuntimeError(
            "InferenceContext is not initialized. "
            "The application lifespan startup did not complete successfully."
        )
    return _CTX
