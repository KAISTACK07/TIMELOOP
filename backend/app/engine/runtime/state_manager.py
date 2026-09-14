from typing import Dict, Any, List
import copy
import pickle

from ..serializer import safe_serialize


class StateManager:
    def __init__(self):
        self.variable_history: Dict[str, List] = {}
        self._last_snapshots: Dict[str, Any] = {}

    def _changed(self, current_val: Any, old_val: Any) -> bool:
        """Canonical replay-state comparison (never UI serialization)."""
        if current_val is old_val:
            return False
        try:
            return current_val != old_val
        except Exception:
            # Conservative fallback for objects with non-standard equality.
            return True

    def _snapshot_value(self, value: Any) -> Any:
        """Freeze current runtime value for replay fidelity."""
        try:
            frozen = copy.deepcopy(value)
            # Worker response crosses process boundary; ensure it can be sent.
            pickle.dumps(frozen)
            return frozen
        except Exception:
            # Keep execution stable for unsupported runtime objects.
            return safe_serialize(value)

    def has_delta(self, current_scope: Dict[str, Any]) -> bool:
        for var_name, current_val in current_scope.items():
            if var_name.startswith("__"):
                continue
            if var_name not in self._last_snapshots:
                return True
            if self._changed(current_val, self._last_snapshots[var_name]):
                return True
        return False

    def compute_delta(self, current_scope: Dict[str, Any]) -> Dict[str, Any]:
        """Return changed vars using replay-canonical snapshots."""
        delta = {}
        for var_name, current_val in current_scope.items():
            if var_name.startswith("__"):
                continue
            old_val = self._last_snapshots.get(var_name)
            if var_name in self._last_snapshots and not self._changed(current_val, old_val):
                continue
            delta[var_name] = self._snapshot_value(current_val)
        return delta

    def commit_delta(self, delta: Dict[str, Any], step: int):
        """Commit a delta to the variable history.
        Only called for events that survive filtering."""
        for var_name, snapshot_val in delta.items():
            self._last_snapshots[var_name] = snapshot_val
            # Track evolution: [[step, value], ...]
            if var_name not in self.variable_history:
                self.variable_history[var_name] = []
            self.variable_history[var_name].append([step, snapshot_val])
