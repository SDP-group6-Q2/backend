"""Makes the `assistant` git submodule importable on its own terms.

The submodule is developed and run standalone (from within `assistant/`,
where its code does `from src.xxx import ...`, treating `assistant/src` as a
top-level `src` package). To reuse it here without patching its internals,
we add `assistant/` to sys.path so those same absolute `src.*` imports
resolve identically inside the backend process.

Import this module (for its side effect) before importing anything from
`src.*`.
"""

import sys
from pathlib import Path

ASSISTANT_DIR = Path(__file__).resolve().parents[2] / "assistant"

if str(ASSISTANT_DIR) not in sys.path:
    sys.path.insert(0, str(ASSISTANT_DIR))
