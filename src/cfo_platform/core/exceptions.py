"""Shared exception hierarchy for cfo_platform."""

from __future__ import annotations


class CfoPlatformError(Exception):
    """Base class for all cfo_platform errors."""


class ConfigurationError(CfoPlatformError):
    """Settings or client configuration is missing or invalid."""


class ClientNotFoundError(CfoPlatformError):
    """No config/clients/<client_id>.yaml exists for the given client_id."""


class ReconciliationError(CfoPlatformError):
    """A computed figure failed to reconcile to its source-report total.

    This is the platform-level expression of the project's most important
    rule (see CLAUDE.md rule 1): analytics and reporting code must raise this
    rather than silently ship a number that doesn't tie back to source.
    """
