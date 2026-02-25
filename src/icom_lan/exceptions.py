"""Custom exception hierarchy for icom-lan."""

__all__ = [
    "IcomLanError",
    "ConnectionError",
    "AuthenticationError",
    "CommandError",
    "TimeoutError",
]


class IcomLanError(Exception):
    """Base exception for all icom-lan errors."""


class ConnectionError(IcomLanError):
    """Raised when a connection to the radio fails or is lost."""


class AuthenticationError(IcomLanError):
    """Raised when authentication with the radio fails."""


class CommandError(IcomLanError):
    """Raised when a CI-V command fails or returns an error."""


class TimeoutError(IcomLanError):
    """Raised when an operation times out."""
