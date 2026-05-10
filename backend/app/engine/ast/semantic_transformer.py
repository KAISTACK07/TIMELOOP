"""
Semantic Transformer — placeholder for future AST-level semantic hints.

IMPORTANT: This transformer must remain GENERIC.  It must NOT contain
algorithm-specific logic (no N-Queens knowledge, no sorting awareness, etc.).

Its purpose is to detect *structural* patterns in user code that
suggest semantic events (e.g. a function named 'solve' returning True
might indicate 'solution_found'), but the actual semantic interpretation
is done downstream in the event processor / reduced mode.

Currently a no-op stub.  Future work may add:
  • Detection of recursive base-case returns
  • Detection of append/remove patterns on tracked containers
"""

import ast
from .base_transformer import BaseInstrumenterMixin


class SemanticTransformerMixin(BaseInstrumenterMixin):
    """Placeholder — no transformations yet.

    This mixin will be added to the Instrumenter class in
    ast_instrumenter.py when semantic AST hints are needed.
    """
    pass
