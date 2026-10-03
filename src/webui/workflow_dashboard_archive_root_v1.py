"""TRANSITIONAL_COMPAT (LEGACY_DELETE_NEXT_WP): re-export neutral archive-root resolver.

CURRENT productive resolution lives in ``src.ops.presentation_archive_root_v1``.
This module preserves legacy import paths for scheduled dashboard deletion WP.
"""

from src.ops.presentation_archive_root_v1.resolver_v1 import *  # noqa: F403
