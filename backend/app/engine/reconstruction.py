import bisect

def reconstruct_state(snapshots, target_step):
    if not snapshots:
        return {}

    # Extract steps list
    steps = [snap["step"] for snap in snapshots]

    # Binary search to find closest index <= target_step
    idx = bisect.bisect_right(steps, target_step) - 1

    if idx < 0:
        return {}

    # Walk backward to find nearest checkpoint
    while idx >= 0 and not snapshots[idx].get("is_full"):
        idx -= 1

    if idx < 0:
        return {}

    checkpoint = snapshots[idx]
    state = dict(checkpoint.get("locals", {}))
    start_step = checkpoint["step"]

    # Apply deltas forward from checkpoint
    for i in range(idx + 1, len(snapshots)):
        snap = snapshots[i]
        step_val = snap["step"]

        if step_val > target_step:
            break

        delta = snap.get("delta", {})
        for k, v in delta.items():
            if v == "__deleted__":
                state.pop(k, None)
            else:
                state[k] = v

    return state