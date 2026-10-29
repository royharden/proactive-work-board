"""Compile the dependency-only B2 subset to exact P01 actions and writes."""

from typing import Any


def compile_dependency(
    task_id: str, links: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    # All links must have been justified by current scoped evidence before here.
    # Two deletions plus ready consume the complete three-domain-write allowance.
    if not 1 <= len(links) <= 2:
        raise ValueError("dependency_write_cap")
    actions: list[dict[str, Any]] = []
    writes: list[dict[str, Any]] = []
    targets: set[str] = set()
    link_ids: set[str] = set()
    for link in sorted(links, key=lambda row: row["id"]):
        dep = link.get("dependency_task_id")
        if (link.get("task_id") != task_id or not isinstance(dep, str) or not dep
                or dep == task_id or dep in targets or link["id"] in link_ids):
            raise ValueError("contradictory_dependency")
        targets.add(dep)
        link_ids.add(link["id"])
        actions.append({
            "action_kind": "clear_dependency", "task_id": task_id,
            "dependency_link_id": link["id"], "dependency_task_id": dep,
        })
        writes.append({
            "op": "delete", "kind": "dependency_links", "id": link["id"],
            "task_id": task_id, "dependency_task_id": dep,
        })
    actions.append({"action_kind": "set_ready", "task_id": task_id})
    writes.append({
        "op": "update", "kind": "tasks", "id": task_id,
        "field": "status", "value": "ready",
    })
    return actions, writes
