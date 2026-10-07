"""Exceptions for the Intelligence Layer providers."""

from typing import Optional


class ProviderError(Exception):
    """Raised when an external or internal provider encounters an error."""

    def __init__(
        self,
        message: str,
        provider_name: str = "unknown",
        status_code: Optional[int] = None,
    ) -> None:
        self.message = message
        self.provider_name = provider_name
        self.status_code = status_code
        super().__init__(f"[{provider_name}] {message}" + (f" (HTTP {status_code})" if status_code else ""))
