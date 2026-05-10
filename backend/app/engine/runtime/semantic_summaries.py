SUMMARY_TEMPLATES = {
    "branch_exhausted": "Search branch exhausted after {count} failed attempts",
    "queen_removed": "Backtracking triggered after {count} conflicts",
    "row_started": "Solver advanced through {count} row transitions",
    "backtrack": "Exploration backtracked {count} times",
    "node_visited": "Traversed {count} nodes in the graph",
}

def get_summary(event_name: str, count: int) -> str:
    template = SUMMARY_TEMPLATES.get(event_name, "{count} {event_name} events")
    return template.format(count=count, event_name=event_name)
