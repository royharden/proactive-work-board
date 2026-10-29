"""Typed observable records for the demo snapshot envelope, without study labels."""
from __future__ import annotations

import re

from .validation import KINDS, STATUSES, TOPICS, closed, identifier, integer, row_ref

FIELDS = {
    "projects": "id version title",
    "tasks": "id version project_id title description status assignee_id not_before_tick wait_reason work_window",
    "people": "id version display_name",
    "dependency_links": "id version task_id dependency_task_id",
    "comments": "id version task_id actor_id body occurred_tick actor_role origin source_event_id source_proposal_id cites topic",
    "documents": "id version project_id task_ids title body effective_interval",
    "availability": "id version person_id available effective_interval",
    "delegations": "id version from_person_id to_person_id scope effective_interval",
}


def interval(value, maximum=97):
    closed(value, "start_tick end_tick")
    integer(value["start_tick"], 0, 96)
    integer(value["end_tick"], 1, maximum)
    if value["start_tick"] >= value["end_tick"]:
        raise ValueError("empty_interval")


def initial_identifier(value):
    identifier(value)
    if len(value) > 128 or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", value) is None:
        raise ValueError("initial_record_id_profile")


def validate_record(kind, row):
    if kind not in KINDS:
        raise ValueError("unsupported_kind")
    closed(row, FIELDS[kind])
    initial_identifier(row["id"])
    integer(row["version"], 1)
    for key in ("title", "description", "display_name", "body"):
        if key in row and (not isinstance(row[key], str) or not 1 <= len(row[key]) <= 4000):
            raise ValueError("record_text")
    for key in ("project_id", "task_id", "dependency_task_id", "person_id", "from_person_id", "to_person_id"):
        if key in row:
            identifier(row[key])
    if kind == "tasks":
        if row["status"] not in STATUSES:
            raise ValueError("task_status")
        if row["assignee_id"] is not None:
            identifier(row["assignee_id"])
        if row["not_before_tick"] is not None:
            integer(row["not_before_tick"], 0, 96)
        if row["wait_reason"] is not None:
            identifier(row["wait_reason"])
        if row["work_window"] is not None:
            interval(row["work_window"], 96)
    if "effective_interval" in row:
        interval(row["effective_interval"])
    if kind == "availability" and type(row["available"]) is not bool:
        raise ValueError("availability_boolean")
    if kind == "delegations":
        closed(row["scope"], "kind id")
        if row["scope"]["kind"] not in ("task", "project"):
            raise ValueError("delegation_scope")
        identifier(row["scope"]["id"])
    if kind == "documents":
        if not isinstance(row["task_ids"], list) or len(set(row["task_ids"])) != len(row["task_ids"]):
            raise ValueError("document_tasks")
        for task in row["task_ids"]:
            identifier(task)
    if kind == "comments":
        integer(row["occurred_tick"], 0, 96)
        role, origin = row["actor_role"], row["origin"]
        if role not in ("human", "world", "agent", "rules") or origin not in ("initial", "exogenous", "arm"):
            raise ValueError("comment_provenance")
        if role == "human":
            identifier(row["actor_id"])
        elif row["actor_id"] is not None:
            raise ValueError("nonperson_actor_id")
        if origin == "arm":
            if role not in ("agent", "rules") or row["source_event_id"] is not None:
                raise ValueError("arm_provenance")
            identifier(row["source_proposal_id"])
        else:
            if role not in ("human", "world") or row["source_proposal_id"] is not None:
                raise ValueError("source_provenance")
            if origin == "initial":
                if row["source_event_id"] is not None or row["occurred_tick"] != 0:
                    raise ValueError("initial_provenance")
            else:
                identifier(row["source_event_id"])
        if row["topic"] is not None and row["topic"] not in TOPICS:
            raise ValueError("comment_topic")
        if not isinstance(row["cites"], list):
            raise ValueError("comment_citations")
        for ref in row["cites"]:
            row_ref(ref, True)
            initial_identifier(ref["id"])


def validate_graph(records):
    if not isinstance(records, dict) or set(records) != set(KINDS):
        raise ValueError("record_kinds")
    indexes = {}
    for kind in KINDS:
        if not isinstance(records[kind], list):
            raise ValueError("record_array")
        indexes[kind] = {}
        for row in records[kind]:
            validate_record(kind, row)
            if row["id"] in indexes[kind]:
                raise ValueError("duplicate_record")
            indexes[kind][row["id"]] = row
    def exists(kind, key):
        if key not in indexes[kind]:
            raise ValueError("record_foreign_key")
    for task in records["tasks"]:
        exists("projects", task["project_id"])
        if task["assignee_id"] is not None:
            exists("people", task["assignee_id"])
    edges = {task: [] for task in indexes["tasks"]}
    for link in records["dependency_links"]:
        exists("tasks", link["task_id"])
        exists("tasks", link["dependency_task_id"])
        edges[link["task_id"]].append(link["dependency_task_id"])
    active, complete = set(), set()
    def visit(task):
        if task in active:
            raise ValueError("dependency_cycle")
        if task not in complete:
            active.add(task)
            for target in edges[task]:
                visit(target)
            active.remove(task)
            complete.add(task)
    for task in edges:
        visit(task)
    for comment in records["comments"]:
        exists("tasks", comment["task_id"])
        if comment["actor_role"] == "human":
            exists("people", comment["actor_id"])
    for doc in records["documents"]:
        exists("projects", doc["project_id"])
        for task_id in doc["task_ids"]:
            exists("tasks", task_id)
            if indexes["tasks"][task_id]["project_id"] != doc["project_id"]:
                raise ValueError("document_project_scope")
    for availability in records["availability"]:
        exists("people", availability["person_id"])
    for delegation in records["delegations"]:
        exists("people", delegation["from_person_id"])
        exists("people", delegation["to_person_id"])
        exists("tasks" if delegation["scope"]["kind"] == "task" else "projects", delegation["scope"]["id"])
