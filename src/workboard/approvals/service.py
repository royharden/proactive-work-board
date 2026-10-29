"""Exact append-only operator decisions through D1, with no apply/DB ownership."""

from copy import deepcopy
from typing import Any

from workboard.controller.evidence import (
    PolicyRefusal, check_binding, integer, read_snapshot, require_actor,
)
from workboard.controller.intent import semantic_intent
from workboard.controller.compile import compile_dependency
from workboard.schemas.canonical import digest_json, proposal_digest
from workboard.schemas.validation import validate_decision, validate_proposal

_PROPOSAL_FIELDS = frozenset({
    "proposal_id", "board_id", "task_id", "candidate_id", "action_bundle", "intent",
    "read_binding", "evidence_refs", "compiled_write_set", "digest", "predicted_summary",
    "expires_tick",
})
_DECISION_FIELDS = frozenset({
    "decision_id", "proposal_id", "board_id", "proposal_digest", "read_binding",
    "operator_label", "actor_kind", "status", "decided_tick", "expires_tick",
})


def _check_proposal(proposal: dict[str, Any]) -> None:
    # Reuse accepted D1 closed wire validation; local guard narrows to B2.
    validate_proposal(proposal)
    if not isinstance(proposal, dict) or set(proposal) != _PROPOSAL_FIELDS:
        raise ValueError("proposal_fields_mismatch")
    if proposal.get("digest") != proposal_digest(proposal):
        raise ValueError("proposal_digest_mismatch")
    expected = semantic_intent(
        proposal["board_id"], proposal["task_id"], proposal["action_bundle"],
        proposal["intent"]["episode_epoch"],
    )
    if expected != proposal["intent"]:
        raise ValueError("intent_mismatch")
    links = []
    for action in proposal["action_bundle"]:
        if action.get("action_kind") == "clear_dependency":
            links.append({
                "id": action["dependency_link_id"], "task_id": action["task_id"],
                "dependency_task_id": action["dependency_task_id"],
            })
    actions, writes = compile_dependency(proposal["task_id"], links)
    if actions != proposal["action_bundle"] or writes != proposal["compiled_write_set"]:
        raise ValueError("dependency_compile_mismatch")
    binding = proposal["read_binding"]
    start = integer(binding["effective_from_tick"])
    end = integer(binding["effective_until_tick"])
    expiry = integer(proposal["expires_tick"])
    if not start < end or not start < expiry <= end:
        raise ValueError("proposal_effective_interval")


def decide(
    store: Any, proposal: dict[str, Any], operator: dict[str, Any], choice: str, tick: int,
) -> dict[str, Any]:
    """Read-only freshness check, then append exact decision metadata through host.

    Operator needs read+decide capabilities on this board. D1 record_decision
    validates against its stored proposal; D1 apply repeats current checks inside
    its own transaction. This function neither consumes approval nor mutates rows.
    """
    proposal = deepcopy(proposal)
    _check_proposal(proposal)
    require_actor(operator, proposal["board_id"], "read", "decide")
    if choice not in {"approved", "rejected"}:
        raise ValueError("operator_choice_required")
    integer(tick)
    snapshot, _ = read_snapshot(
        store, proposal["board_id"], proposal["task_id"], operator,
        expected_epoch=proposal["intent"]["episode_epoch"],
    )
    if snapshot["tick"] != tick:
        raise PolicyRefusal("operator_tick_mismatch")
    check_binding(proposal, snapshot)
    decision = {
        "decision_id": "decision_" + digest_json([
            proposal["proposal_id"], proposal["digest"], operator["label"],
            operator["kind"], choice, tick,
        ])[:32],
        "proposal_id": proposal["proposal_id"], "board_id": proposal["board_id"],
        "proposal_digest": proposal["digest"], "read_binding": deepcopy(proposal["read_binding"]),
        "operator_label": operator["label"], "actor_kind": operator["kind"],
        "status": choice, "decided_tick": tick, "expires_tick": proposal["expires_tick"],
    }
    store.record_decision(deepcopy(decision), operator)
    return decision


def approved_bundle(proposal: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    """Package an exact approved P01 envelope, not an apply authorization check.

    No store access here: consumption, supersession/rejection and current time,
    versions/absence/capabilities are rechecked only by the atomic D1 apply path.
    """
    proposal, decision = deepcopy(proposal), deepcopy(decision)
    _check_proposal(proposal)
    validate_decision(decision)
    if not isinstance(decision, dict) or set(decision) != _DECISION_FIELDS:
        raise ValueError("decision_fields_mismatch")
    if (decision["status"] != "approved"
            or decision["proposal_id"] != proposal["proposal_id"]
            or decision["board_id"] != proposal["board_id"]
            or decision["proposal_digest"] != proposal["digest"]
            or decision["read_binding"] != proposal["read_binding"]
            or decision["actor_kind"] not in {"human", "scripted"}
            or not isinstance(decision["operator_label"], str) or not decision["operator_label"].strip()):
        raise ValueError("decision_proposal_binding_mismatch")
    tick = integer(decision["decided_tick"])
    expiry = integer(decision["expires_tick"])
    binding = proposal["read_binding"]
    if not binding["effective_from_tick"] <= tick < expiry <= proposal["expires_tick"]:
        raise ValueError("decision_expired_or_outside_binding")
    return {"proposal": proposal, "decision": decision}
