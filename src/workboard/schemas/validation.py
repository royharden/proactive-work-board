"""Closed P01 wire checks and public normalization; no controller imports."""
from __future__ import annotations

import re
from .canonical import canonical_json, digest_json, proposal_digest

KINDS = ("projects", "tasks", "dependency_links", "comments", "documents", "people", "availability", "delegations")
STATUSES = ("todo", "blocked", "ready", "in_progress", "done", "parked")
TOPICS = ("decision_record", "dependency_state", "delegation_scope", "availability_window", "work_window")
ACTIONS = ("clear_dependency", "set_ready", "reassign_to_delegate", "request_info", "evidence_comment")
CAPABILITIES = ("tasks", "dependency_links", "comments", "documents", "availability", "delegations",
                "atomic_bundle_cas", "evidence_scope_revision", "intent_receipts", "virtual_clock")


def closed(value, fields):
    if not isinstance(value, dict) or set(value) != set(fields.split()):
        raise ValueError("closed_shape")


def identifier(value):
    if not isinstance(value, str) or not value:
        raise ValueError("identifier")


def integer(value, low=0, high=None):
    if type(value) is not int or value < low or (high is not None and value > high):
        raise ValueError("integer_range")


def digest(value):
    if not isinstance(value, str) or re.fullmatch(r"[a-f0-9]{64}", value) is None:
        raise ValueError("digest")


def row_ref(value, evidence=False):
    closed(value, "kind id version digest" if evidence else "kind id version")
    if value["kind"] not in KINDS:
        raise ValueError("unsupported_kind")
    identifier(value["id"])
    integer(value["version"])
    if evidence:
        digest(value["digest"])


def binding(value):
    closed(value, "rows evidence_scope_revision effective_from_tick effective_until_tick")
    if not isinstance(value["rows"], list):
        raise ValueError("rows")
    seen = set()
    for row in value["rows"]:
        row_ref(row)
        key = (row["kind"], row["id"])
        if key in seen:
            raise ValueError("duplicate_read_row")
        seen.add(key)
    integer(value["evidence_scope_revision"])
    integer(value["effective_from_tick"], 0, 96)
    integer(value["effective_until_tick"], 0, 96)
    if value["effective_from_tick"] >= value["effective_until_tick"]:
        raise ValueError("empty_effective_interval")


def write(value, *, scripted=False):
    if not isinstance(value, dict):
        raise ValueError("write")
    op, kind = value.get("op"), value.get("kind")
    if op == "delete" and kind == "dependency_links":
        closed(value, "op kind id task_id dependency_task_id")
        identifier(value["task_id"])
        identifier(value["dependency_task_id"])
    elif op == "update" and kind == "tasks":
        closed(value, "op kind id field value")
        field, target = value["field"], value["value"]
        if field == "status":
            if target not in (STATUSES if scripted else ("ready",)):
                raise ValueError("unsupported_status")
        elif field == "assignee_id":
            identifier(target)
        else:
            raise ValueError("unsupported_field")
    elif op == "insert" and kind == "comments":
        closed(value, "op kind id task_id actor_role body cites topic")
        identifier(value["task_id"])
        if value["actor_role"] not in (("world",) if scripted else ("agent", "rules")):
            raise ValueError("comment_actor_role")
        if not isinstance(value["body"], str) or not 1 <= len(value["body"]) <= 4000:
            raise ValueError("comment_body")
        if value["topic"] is not None and value["topic"] not in TOPICS:
            raise ValueError("comment_topic")
        if not isinstance(value["cites"], list):
            raise ValueError("citations")
        for citation in value["cites"]:
            row_ref(citation, True)
    else:
        raise ValueError("unsupported_write")
    identifier(value["id"])


def validate_writes(values, *, scripted=False):
    if not isinstance(values, list) or not 1 <= len(values) <= 4:
        raise ValueError("write_count")
    domain = comments = 0
    seen = set()
    for value in values:
        write(value, scripted=scripted)
        comments += value["kind"] == "comments"
        domain += value["kind"] != "comments"
        key = (value["kind"], value["id"], value.get("field"))
        if key in seen:
            raise ValueError("duplicate_write")
        seen.add(key)
    if domain > 3 or comments > 1:
        raise ValueError("template_write_cap")


def action(value):
    if not isinstance(value, dict):
        raise ValueError("action")
    kind = value.get("action_kind")
    fields = {
        "clear_dependency": "dependency_link_id dependency_task_id",
        "set_ready": "",
        "reassign_to_delegate": "delegate_id delegation_id availability_id",
        "request_info": "topic body cites",
        "evidence_comment": "body cites",
    }
    if kind not in fields:
        raise ValueError("unsupported_action")
    closed(value, "action_kind task_id " + fields[kind])
    identifier(value["task_id"])
    for name in ("dependency_link_id", "dependency_task_id", "delegate_id", "delegation_id", "availability_id"):
        if name in value:
            identifier(value[name])
    if kind == "request_info" and value["topic"] not in TOPICS:
        raise ValueError("request_topic")
    if "body" in value:
        if not isinstance(value["body"], str) or not 1 <= len(value["body"]) <= 4000:
            raise ValueError("comment_body")
        if not isinstance(value["cites"], list):
            raise ValueError("citations")
        for citation in value["cites"]:
            row_ref(citation, True)
        if kind == "evidence_comment" and not value["cites"]:
            raise ValueError("uncited_comment")


def normalized_intent(board_id, task_id, actions, epoch):
    """Frozen public identity normalization, independently enforced by the host."""
    pairs = []
    classes = []
    for item in actions:
        action(item)
        kind = item["action_kind"]
        classes.append(kind)
        if kind == "clear_dependency":
            target = [item["dependency_task_id"]]
        elif kind == "set_ready":
            target = [task_id, "ready"]
        elif kind == "reassign_to_delegate":
            target = [item["delegate_id"]]
        elif kind == "request_info":
            target = [item["topic"]]
        else:
            target = sorted({(ref["kind"], ref["id"]) for ref in item["cites"]})
            target = [list(pair) for pair in target]
        pairs.append([kind, digest_json(target)])
    if len({canonical_json(pair) for pair in pairs}) != len(pairs):
        raise ValueError("duplicate_normalized_action")
    primary = next(kind for kind in ACTIONS if kind in classes)
    domain = [pair for pair in pairs if pair[0] in ACTIONS[:3]]
    semantic_target = digest_json(sorted(domain or pairs))
    key = digest_json([board_id, task_id, primary, semantic_target, epoch])
    return {"board_id": board_id, "task_id": task_id, "action_kind": primary,
            "semantic_target": semantic_target, "episode_epoch": epoch, "intent_key": key}


def validate_proposal(value):
    closed(value, "proposal_id board_id task_id candidate_id action_bundle intent read_binding evidence_refs compiled_write_set digest predicted_summary expires_tick")
    for name in ("proposal_id", "board_id", "task_id", "candidate_id", "predicted_summary"):
        identifier(value[name])
    binding(value["read_binding"])
    integer(value["expires_tick"], 0, 96)
    digest(value["digest"])
    if proposal_digest(value) != value["digest"]:
        raise ValueError("proposal_digest")
    actions = value["action_bundle"]
    if not isinstance(actions, list) or not 1 <= len(actions) <= 4:
        raise ValueError("action_count")
    for item in actions:
        action(item)
        if item["task_id"] != value["task_id"]:
            raise ValueError("cross_task_action")
    intent = value["intent"]
    closed(intent, "board_id task_id action_kind semantic_target episode_epoch intent_key")
    integer(intent["episode_epoch"])
    if intent != normalized_intent(value["board_id"], value["task_id"], actions, intent["episode_epoch"]):
        raise ValueError("intent_normalization")
    if not isinstance(value["evidence_refs"], list):
        raise ValueError("evidence_refs")
    for ref in value["evidence_refs"]:
        row_ref(ref, True)
    validate_writes(value["compiled_write_set"])
    # Match every permission to one declared action, including exact comment text/citations.
    remaining = list(value["compiled_write_set"])
    for item in actions:
        kind = item["action_kind"]
        if kind == "clear_dependency":
            expected = {"op": "delete", "kind": "dependency_links", "id": item["dependency_link_id"],
                        "task_id": item["task_id"], "dependency_task_id": item["dependency_task_id"]}
        elif kind in ("set_ready", "reassign_to_delegate"):
            expected = {"op": "update", "kind": "tasks", "id": item["task_id"],
                        "field": "status" if kind == "set_ready" else "assignee_id",
                        "value": "ready" if kind == "set_ready" else item["delegate_id"]}
        else:
            matches = [w for w in remaining if w["op"] == "insert" and w["kind"] == "comments"]
            if len(matches) != 1:
                raise ValueError("comment_compile")
            expected = dict(matches[0])
            expected.update(task_id=item["task_id"], body=item["body"], cites=item["cites"],
                            topic=item.get("topic"))
        if expected not in remaining:
            raise ValueError("compile_mismatch")
        remaining.remove(expected)
    if remaining:
        raise ValueError("undeclared_write")


def validate_decision(value):
    closed(value, "decision_id proposal_id board_id proposal_digest read_binding operator_label actor_kind status decided_tick expires_tick")
    for name in ("decision_id", "proposal_id", "board_id", "operator_label"):
        identifier(value[name])
    digest(value["proposal_digest"])
    binding(value["read_binding"])
    if value["status"] not in ("approved", "rejected", "expired", "superseded"):
        raise ValueError("decision_status")
    if value["actor_kind"] not in ("scripted", "human"):
        raise ValueError("decision_actor_kind")
    integer(value["decided_tick"], 0, 96)
    integer(value["expires_tick"], 0, 96)
    if value["status"] == "approved" and value["decided_tick"] >= value["expires_tick"]:
        raise ValueError("decision_interval")
