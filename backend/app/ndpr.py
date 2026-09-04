"""
DEPRECATED — Use app.compliance.ndpa instead.

This module is kept only so old imports do not crash.
The NDPR 2019 ceased to be a legal instrument once the GAID took effect
on 19 September 2025. Carenova now uses NDPA 2023 + GAID 2025 terminology
and rules everywhere — see app/compliance/ndpa.py.
"""
import warnings
from app.compliance.ndpa import NDPACompliance as NDPRCompliance  # noqa: F401

warnings.warn(
    "app.compliance.ndpr is deprecated — NDPR 2019 is no longer in force. "
    "Use app.compliance.ndpa.NDPACompliance instead.",
    DeprecationWarning,
    stacklevel=2,
)
