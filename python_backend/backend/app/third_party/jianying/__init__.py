"""Stable public interface for the embedded Jianying puzzle module.

The implementation in this directory is intentionally isolated.  Callers should
only import ``build_hint_board`` so this folder can be replaced as a unit later.
"""

from .adapter import build_hint_board

__all__ = ["build_hint_board"]
