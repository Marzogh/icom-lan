"""Public package export tests."""

from icom_lan import ScopeCompletionPolicy


def test_scope_completion_policy_exported() -> None:
    assert ScopeCompletionPolicy.VERIFY.value == "verify"
