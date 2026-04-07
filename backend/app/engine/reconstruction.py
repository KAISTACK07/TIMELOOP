def reconstruct_state(snapshots, target_index):
    state = {}

    checkpoint_index = 0

    for i in range(target_index, -1, -1):
        if snapshots[i].get("is_full"):
            checkpoint_index = i
            break

    base_snapshot = snapshots[checkpoint_index]
    state = dict(base_snapshot.get("locals", {}))

    for i in range(checkpoint_index + 1, target_index + 1):
        snap = snapshots[i]

        if snap.get("delta"):
            for k, v in snap["delta"].items():
                if v == "__deleted__":
                    state.pop(k, None)
                else:
                    state[k] = v

    return state