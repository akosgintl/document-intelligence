class TransientProviderError(Exception):
    """A Model Provider call failed for a reason worth retrying with backoff — a rate limit,
    a network failure, or a 5xx — as opposed to a bug in this codebase or a permanent
    rejection from the Provider (ADR-0009). Every Provider implementation raises this same
    type for its own vendor-specific transient conditions, so the retry policy (retry.py)
    never needs vendor-specific exception knowledge.
    """

    def __init__(self, message: str, *, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after
