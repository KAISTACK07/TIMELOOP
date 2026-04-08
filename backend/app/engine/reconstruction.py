def reconstruct_state(snapshots, target_step):
    state = {}
    print("DEBUG target_step:", target_step, type(target_step))
    # 1. Find latest checkpoint BEFORE target_step
    checkpoint = None

    for snap in snapshots:
        print("DEBUG snap step:", snap.get("step"), type(snap.get("step")))
        if snap["step"] > target_step:
            break

        if snap.get("is_full"):
            checkpoint = snap

    # 2. Initialize state
    if checkpoint:
        state = dict(checkpoint.get("locals", {}))
        start_step = checkpoint["step"]
    else:
        state = {}
        start_step = 0

    # 3. Apply deltas forward
    for snap in snapshots:
        if snap["step"] <= start_step:
            continue

        if snap["step"] > target_step:
            break

        delta = snap.get("delta", {})
        for k, v in delta.items():
            if v == "__deleted__":
                state.pop(k, None)
            else:
                state[k] = v

    return state