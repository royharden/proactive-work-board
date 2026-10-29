"""Explicit-path stdlib SQLite host. Construction source; execution is not verified.

All writes require an explicit board-scoped local actor. Actor labels/capability
mappings are demo policy attribution, not authenticated production identities.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import sqlite3

from workboard.apply.controls import PrecommitAbort, PostcommitAckLoss
from workboard.schemas.canonical import canonical_json, digest_json
from workboard.schemas.records import initial_identifier, validate_graph, validate_record
from workboard.schemas.validation import (
    ACTIONS, CAPABILITIES, KINDS, binding, closed, identifier, integer,
    validate_decision, validate_proposal, validate_writes,
)

DDL = (
    "CREATE TABLE IF NOT EXISTS boards (id TEXT PRIMARY KEY, tick INTEGER NOT NULL, revision INTEGER NOT NULL)",
    "CREATE TABLE IF NOT EXISTS records (board TEXT NOT NULL, kind TEXT NOT NULL, id TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(board,kind,id), FOREIGN KEY(board) REFERENCES boards(id))",
    "CREATE TABLE IF NOT EXISTS proposals (board TEXT NOT NULL, id TEXT NOT NULL, payload TEXT NOT NULL, actor TEXT NOT NULL, PRIMARY KEY(board,id), FOREIGN KEY(board) REFERENCES boards(id))",
    "CREATE TABLE IF NOT EXISTS decisions (board TEXT NOT NULL, id TEXT NOT NULL, proposal TEXT NOT NULL, payload TEXT NOT NULL, actor TEXT NOT NULL, consumed INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(board,id), FOREIGN KEY(board,proposal) REFERENCES proposals(board,id))",
    "CREATE TABLE IF NOT EXISTS intents (board TEXT NOT NULL, key TEXT NOT NULL, payload TEXT NOT NULL, receipt TEXT NOT NULL, PRIMARY KEY(board,key), FOREIGN KEY(board) REFERENCES boards(id))",
    "CREATE TABLE IF NOT EXISTS outbox (seq INTEGER PRIMARY KEY AUTOINCREMENT, board TEXT NOT NULL, payload TEXT NOT NULL, FOREIGN KEY(board) REFERENCES boards(id))",
    "CREATE TABLE IF NOT EXISTS history (seq INTEGER PRIMARY KEY AUTOINCREMENT, board TEXT NOT NULL, payload TEXT NOT NULL, FOREIGN KEY(board) REFERENCES boards(id))",
    "CREATE TABLE IF NOT EXISTS policy_reads (board TEXT NOT NULL, task TEXT NOT NULL, episode INTEGER NOT NULL, used INTEGER NOT NULL CHECK(used BETWEEN 1 AND 8), PRIMARY KEY(board,task,episode), FOREIGN KEY(board,task) REFERENCES epochs(board,task))",
    "CREATE TABLE IF NOT EXISTS initial_boundaries (board TEXT PRIMARY KEY, payload TEXT NOT NULL, FOREIGN KEY(board) REFERENCES boards(id))",
    "CREATE TABLE IF NOT EXISTS epochs (board TEXT NOT NULL, task TEXT NOT NULL, epoch INTEGER NOT NULL, PRIMARY KEY(board,task), FOREIGN KEY(board) REFERENCES boards(id))",
)


def _authorize(actor, board_id, capability):
    identifier(board_id)
    closed(actor, "label kind board_ids capabilities")
    identifier(actor["label"])
    if actor["kind"] not in ("scripted", "human"):
        raise PermissionError("actor_kind")
    if not isinstance(actor["board_ids"], list) or not isinstance(actor["capabilities"], list):
        raise PermissionError("actor_scope")
    if board_id not in actor["board_ids"] or capability not in actor["capabilities"]:
        raise PermissionError("actor_capability")
    if any(cap not in ("read", "propose", "decide", "apply", "advance", "seed", "scripted_edit")
           for cap in actor["capabilities"]):
        raise PermissionError("unknown_capability")


class ReadBudgetExceeded(RuntimeError):
    """The durable eight-read controller/approval episode budget is exhausted."""


class BoardStore:
    def __init__(self, db_path):
        path = Path(db_path)
        if not path.is_absolute() or path.suffix.lower() not in (".db", ".sqlite", ".sqlite3"):
            raise ValueError("explicit_absolute_sqlite_path_required")
        path = path.resolve()
        if any("onedrive" in part.lower() for part in path.parts) or path.is_relative_to(Path(__file__).resolve().parents[3]):
            raise ValueError("runtime_database_must_be_outside_onedrive_and_source")
        self.db_path = path
        self.failpoint = None  # None | precommit_abort | postcommit_ack_loss

    @contextmanager
    def _connection(self, *, create=False, write=False):
        if not self.db_path.parent.is_dir():
            raise ValueError("explicit_run_directory_must_exist")
        mode = "rwc" if create else "rw"
        connection = sqlite3.connect(self.db_path.as_uri() + "?mode=" + mode,
                                     uri=True, isolation_level=None, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA synchronous=FULL")
            if create:
                connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _board(c, board_id):
        result = c.execute("SELECT tick,revision FROM boards WHERE id=?", (board_id,)).fetchone()
        if result is None:
            raise ValueError("unknown_board")
        return result

    @staticmethod
    def _record(c, board_id, kind, record_id):
        if kind not in KINDS:
            raise ValueError("unsupported_kind")
        row = c.execute("SELECT payload FROM records WHERE board=? AND kind=? AND id=?",
                        (board_id, kind, record_id)).fetchone()
        return None if row is None else json.loads(row["payload"])

    def _snapshot(self, c, board_id, *, history=True):
        board = self._board(c, board_id)
        records = {kind: [] for kind in KINDS}
        for row in c.execute("SELECT kind,payload FROM records WHERE board=? ORDER BY kind,id", (board_id,)):
            records[row["kind"]].append(json.loads(row["payload"]))
        result = {"board_id": board_id, "tick": board["tick"],
                  "evidence_scope_revision": board["revision"], "records": records}
        if history:
            entries = [json.loads(row["payload"]) for row in
                c.execute("SELECT payload FROM history WHERE board=? ORDER BY seq", (board_id,))]
            result["effect_history"] = entries
            result["history_complete"] = self._history_complete(c, board_id, result, entries)
        return result

    @staticmethod
    def _core_digest(core, board_id):
        closed(core, "board_id tick evidence_scope_revision records")
        if core["board_id"] != board_id:
            raise ValueError("history_board_scope")
        integer(core["tick"], 0, 96)
        integer(core["evidence_scope_revision"])
        validate_graph(core["records"])
        for rows in core["records"].values():
            if rows != sorted(rows, key=lambda row: row["id"]):
                raise ValueError("history_core_order")
        return digest_json(core)

    def _history_complete(self, c, board_id, observation, entries):
        """Derive chronology completeness; this is not semantic verification.

        Legacy/partial stores stay explicitly incomplete. No retrospective seed,
        missing-step interpolation, or caller-provided success flag is accepted.
        """
        if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='initial_boundaries'").fetchone():
            return False
        anchor = c.execute("SELECT payload FROM initial_boundaries WHERE board=?", (board_id,)).fetchone()
        if anchor is None or not entries:
            return False
        try:
            initial = json.loads(anchor["payload"])
            initial_digest = self._core_digest(initial, board_id)
            if initial["tick"] != 0 or initial["evidence_scope_revision"] != 0:
                return False
            previous, previous_digest = initial, None
            for index, entry in enumerate(entries):
                a, b = entry["before"], entry["after"]
                if (entry["observation_seq"] != index or entry["previous_digest"] != previous_digest
                        or entry["actor_kind"] not in ("world", "human", "rules", "agent")
                        or not isinstance(entry["actor_label"], str) or not entry["actor_label"]):
                    return False
                if self._core_digest(a, board_id) != self._core_digest(previous, board_id):
                    return False
                self._core_digest(b, board_id)
                if b["tick"] < a["tick"] or b["evidence_scope_revision"] < a["evidence_scope_revision"]:
                    return False
                kind = entry["entry_kind"]
                if index == 0:
                    if (kind != "seed" or digest_json(a) != initial_digest
                            or digest_json(b) != initial_digest or "receipt" in entry):
                        return False
                elif kind == "clock":
                    if (b["tick"] <= a["tick"] or b["records"] != a["records"]
                            or b["evidence_scope_revision"] != a["evidence_scope_revision"]
                            or "receipt" in entry):
                        return False
                elif kind in ("apply", "scripted_edit"):
                    if (b["tick"] != a["tick"] or b["records"] == a["records"]
                            or b["evidence_scope_revision"] <= a["evidence_scope_revision"]):
                        return False
                    if kind == "apply":
                        receipt, proposal, decision = entry["receipt"], entry["proposal"], entry["decision"]
                        stored = c.execute("SELECT receipt FROM intents WHERE board=? AND key=?",
                                           (board_id, receipt["intent_key"])).fetchone()
                        journal_p = c.execute("SELECT payload FROM proposals WHERE board=? AND id=?",
                                              (board_id, receipt["proposal_id"])).fetchone()
                        journal_d = c.execute("SELECT payload,consumed FROM decisions WHERE board=? AND id=?",
                                              (board_id, receipt["decision_id"])).fetchone()
                        if (stored is None or json.loads(stored["receipt"]) != receipt
                                or journal_p is None or json.loads(journal_p["payload"]) != proposal
                                or journal_d is None or json.loads(journal_d["payload"]) != decision
                                or journal_d["consumed"] != 1 or receipt["board_id"] != board_id
                                or receipt["status"] != "applied" or receipt["committed"] is not True
                                or receipt["applied_tick"] != b["tick"]):
                            return False
                    elif "receipt" in entry:
                        return False
                else:
                    return False
                previous, previous_digest = b, digest_json(entry)
            core = {key: observation[key] for key in ("board_id", "tick", "evidence_scope_revision", "records")}
            return self._core_digest(previous, board_id) == self._core_digest(core, board_id)
        except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
            return False

    def _append_history(self, c, board_id, kind, before, after, actor_kind, actor_label, **extra):
        """Persist an actual transition inside its mutation transaction."""
        self._core_digest(before, board_id)
        self._core_digest(after, board_id)
        last = c.execute("SELECT payload FROM history WHERE board=? ORDER BY seq DESC LIMIT 1", (board_id,)).fetchone()
        previous = None if last is None else json.loads(last["payload"])
        # Old incomplete databases are never repaired by fabricating an anchor.
        sequence = 0 if previous is None else previous.get("observation_seq", -1) + 1
        entry = {"entry_kind": kind, "observation_seq": sequence,
                 "previous_digest": None if previous is None else digest_json(previous),
                 "before": before, "after": after, "actor_kind": actor_kind,
                 "actor_label": actor_label, **extra}
        c.execute("INSERT INTO history(board,payload) VALUES (?,?)", (board_id, canonical_json(entry)))

    def initialize(self, board, actor):
        board = deepcopy(board)
        closed(board, "board_id tick evidence_scope_revision records")
        _authorize(actor, board["board_id"], "seed")
        initial_identifier(board["board_id"])
        if actor["kind"] != "scripted":
            raise PermissionError("seed_is_scripted_only")
        integer(board["tick"], 0, 0)
        integer(board["evidence_scope_revision"], 0, 0)
        validate_graph(board["records"])
        if any(row["origin"] != "initial" for row in board["records"]["comments"]):
            raise ValueError("initial_comment_origin")
        with self._connection(create=True, write=True) as c:
            for statement in DDL:
                c.execute(statement)
            if c.execute("SELECT 1 FROM boards WHERE id=?", (board["board_id"],)).fetchone():
                raise ValueError("board_already_exists")
            c.execute("INSERT INTO boards VALUES (?,?,?)", (board["board_id"], 0, 0))
            for kind, rows in board["records"].items():
                for row in rows:
                    self._put(c, board["board_id"], kind, row)
            for task in board["records"]["tasks"]:
                c.execute("INSERT INTO epochs VALUES (?,?,0)", (board["board_id"], task["id"]))
            initial = self._snapshot(c, board["board_id"], history=False)
            c.execute("INSERT INTO initial_boundaries VALUES (?,?)",
                      (board["board_id"], canonical_json(initial)))
            self._append_history(c, board["board_id"], "seed", initial, deepcopy(initial),
                                 "world", actor["label"])

    def capabilities(self):
        return list(CAPABILITIES)

    def snapshot(self, board_id, actor):
        _authorize(actor, board_id, "read")
        with self._connection() as c:
            return self._snapshot(c, board_id)

    def verification_snapshot(self, board_id, proposal_id, decision_id, actor):
        """Read a consistent core/history plus exact board-local journal context.

        Call before apply; later/stale context remains subject to the verifier's
        independent binding checks. This never invents a proposal or decision.
        """
        _authorize(actor, board_id, "read")
        with self._connection() as c:
            proposal = c.execute("SELECT payload FROM proposals WHERE board=? AND id=?",
                                 (board_id, proposal_id)).fetchone()
            decision = c.execute("SELECT payload FROM decisions WHERE board=? AND id=? AND proposal=?",
                                 (board_id, decision_id, proposal_id)).fetchone()
            if proposal is None or decision is None:
                raise ValueError("missing_verification_context")
            result = self._snapshot(c, board_id)
            result["verification_context"] = {"proposal": json.loads(proposal["payload"]),
                                               "decision": json.loads(decision["payload"])}
            return result

    def read_task(self, board_id, task_id, actor):
        return self.read_record(board_id, "tasks", task_id, actor)

    def read_record(self, board_id, kind, id, actor):
        _authorize(actor, board_id, "read")
        with self._connection() as c:
            self._board(c, board_id)
            return self._record(c, board_id, kind, id)

    def read_events(self, board_id, after_seq, limit, actor):
        _authorize(actor, board_id, "read")
        integer(after_seq)
        integer(limit, 1, 100)
        with self._connection() as c:
            self._board(c, board_id)
            return [json.loads(row["payload"]) for row in c.execute(
                "SELECT payload FROM outbox WHERE board=? AND seq>? ORDER BY seq LIMIT ?",
                (board_id, after_seq, limit))]

    def search_text(self, board_id, task_id, query, limit, actor):
        """Bounded task/project observation; D2 owns the eight-call episode budget."""
        _authorize(actor, board_id, "read")
        identifier(query)
        integer(limit, 1, 8)
        with self._connection() as c:
            task = self._record(c, board_id, "tasks", task_id)
            if task is None:
                return {"records": [], "truncated": False}
            matches = []
            for kind in ("comments", "documents"):
                for row in c.execute("SELECT payload FROM records WHERE board=? AND kind=? ORDER BY id", (board_id, kind)):
                    record = json.loads(row["payload"])
                    related = (record["task_id"] == task_id if kind == "comments" else
                               record["project_id"] == task["project_id"] and task_id in record["task_ids"])
                    if related and query.casefold() in record["body"].casefold():
                        matches.append({"kind": kind, "record": record})
            return {"records": matches[:limit], "truncated": len(matches) > limit}

    def reserve_read(self, board_id, task_id, actor):
        """Durably charge the next controller/approval read BEFORE dispatch.

        This returns metadata only, never a domain snapshot. A committed charge
        remains spent after a failed/empty query, client crash or store reopening.
        Labels and store objects cannot reset the board/task/host-epoch key.
        Callers must reserve before every policy/approval domain read; observer
        snapshots used by the driver/verifier are not automatically charged.
        No fallback budget or inferred epoch is accepted.
        """
        _authorize(actor, board_id, "read")
        _authorize(actor, board_id, "propose" if "propose" in actor["capabilities"] else "decide")
        identifier(task_id)
        with self._connection(write=True) as c:
            self._board(c, board_id)  # Board metadata only.
            observed = c.execute("SELECT epoch FROM epochs WHERE board=? AND task=?",
                                 (board_id, task_id)).fetchone()
            if observed is None:
                raise ValueError("unknown_task_episode")
            epoch = observed["epoch"]
            integer(epoch)
            # Missing metadata tables fail closed; never recreate a lost journal
            # on this read path or substitute an in-memory zero.
            if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='policy_reads'").fetchone():
                raise RuntimeError("durable_read_journal_unavailable")
            row = c.execute("SELECT used FROM policy_reads WHERE board=? AND task=? AND episode=?",
                            (board_id, task_id, epoch)).fetchone()
            used = 0 if row is None else row["used"]
            integer(used, 0, 8)
            if used >= 8:
                raise ReadBudgetExceeded("eight_read_episode_limit")
            charged = used + 1
            c.execute("INSERT INTO policy_reads(board,task,episode,used) VALUES (?,?,?,?) "
                      "ON CONFLICT(board,task,episode) DO UPDATE SET used=excluded.used",
                      (board_id, task_id, epoch, charged))
            result = {"episode_epoch": epoch, "reads_used": charged, "reads_remaining": 8 - charged}
        # Returning only after successful COMMIT prevents dispatch on failed charge.
        return result

    def episode_epoch(self, board_id, task_id, actor):
        """Optional observation helper for consumers regenerating a real episode."""
        _authorize(actor, board_id, "read")
        with self._connection() as c:
            self._board(c, board_id)
            row = c.execute("SELECT epoch FROM epochs WHERE board=? AND task=?", (board_id, task_id)).fetchone()
            if row is None:
                raise ValueError("unknown_task")
            return row["epoch"]

    @staticmethod
    def _put(c, board_id, kind, row):
        validate_record(kind, row)
        c.execute("INSERT INTO records(board,kind,id,payload) VALUES (?,?,?,?) "
                  "ON CONFLICT(board,kind,id) DO UPDATE SET payload=excluded.payload",
                  (board_id, kind, row["id"], canonical_json(row)))

    def _check_binding(self, c, proposal, *, require_epoch=True):
        board_id, tick = proposal["board_id"], self._board(c, proposal["board_id"])["tick"]
        bound = proposal["read_binding"]
        binding(bound)
        if self._board(c, board_id)["revision"] != bound["evidence_scope_revision"]:
            raise ValueError("stale")
        if not bound["effective_from_tick"] <= tick < min(bound["effective_until_tick"], proposal["expires_tick"]):
            raise ValueError("expired")
        rows = {(row["kind"], row["id"]): row["version"] for row in bound["rows"]}
        for (kind, id), version in rows.items():
            row = self._record(c, board_id, kind, id)
            if row is None or row["version"] != version:
                raise ValueError("stale")
        for evidence in proposal["evidence_refs"]:
            row = self._record(c, board_id, evidence["kind"], evidence["id"])
            if (row is None or row["version"] != evidence["version"] or
                    digest_json(row) != evidence["digest"] or
                    rows.get((evidence["kind"], evidence["id"])) != evidence["version"]):
                raise ValueError("stale_evidence")
            if "effective_interval" in row:
                period = row["effective_interval"]
                if not period["start_tick"] <= tick < period["end_tick"]:
                    raise ValueError("expired_evidence")
        task = self._record(c, board_id, "tasks", proposal["task_id"])
        if task is None:
            raise ValueError("unknown_task")
        # Conservative full policy input closure, including evidence of absence.
        required = {("tasks", task["id"]), ("projects", task["project_id"])}
        snapshot = self._snapshot(c, board_id, history=False)["records"]
        for kind in ("people", "availability", "delegations"):
            required.update((kind, row["id"]) for row in snapshot[kind])
        for row in snapshot["dependency_links"]:
            if row["task_id"] == task["id"]:
                required.add(("dependency_links", row["id"]))
                required.add(("tasks", row["dependency_task_id"]))
        required.update(("comments", row["id"]) for row in snapshot["comments"] if row["task_id"] == task["id"])
        required.update(("documents", row["id"]) for row in snapshot["documents"] if row["project_id"] == task["project_id"])
        if not required.issubset(rows):
            raise ValueError("incomplete_read_set")
        for action in proposal["action_bundle"]:
            for ref in action.get("cites", []):
                if ref not in proposal["evidence_refs"]:
                    raise ValueError("unbound_citation")
        if require_epoch:
            epoch = c.execute("SELECT epoch FROM epochs WHERE board=? AND task=?", (board_id, task["id"])).fetchone()
            if epoch is None or epoch["epoch"] != proposal["intent"]["episode_epoch"]:
                raise ValueError("stale_epoch")

    def register_proposal(self, proposal, actor):
        proposal = deepcopy(proposal)
        validate_proposal(proposal)
        _authorize(actor, proposal["board_id"], "propose")
        with self._connection(write=True) as c:
            if self._board(c, proposal["board_id"])["tick"] >= 72:
                raise ValueError("proposal_horizon")
            self._check_binding(c, proposal)
            old = c.execute("SELECT payload,actor FROM proposals WHERE board=? AND id=?",
                            (proposal["board_id"], proposal["proposal_id"])).fetchone()
            if old:
                if old["payload"] == canonical_json(proposal) and old["actor"] == canonical_json(actor):
                    return
                raise ValueError("proposal_id_conflict")
            c.execute("INSERT INTO proposals VALUES (?,?,?,?)",
                      (proposal["board_id"], proposal["proposal_id"], canonical_json(proposal), canonical_json(actor)))

    def record_decision(self, decision, actor):
        decision = deepcopy(decision)
        validate_decision(decision)
        _authorize(actor, decision["board_id"], "decide")
        if actor["label"] != decision["operator_label"] or actor["kind"] != decision["actor_kind"]:
            raise PermissionError("decision_attribution")
        with self._connection(write=True) as c:
            tick = self._board(c, decision["board_id"])["tick"]
            if decision["decided_tick"] != tick:
                raise ValueError("decision_tick")
            stored = c.execute("SELECT payload FROM proposals WHERE board=? AND id=?",
                               (decision["board_id"], decision["proposal_id"])).fetchone()
            if stored is None:
                raise ValueError("unknown_proposal")
            proposal = json.loads(stored["payload"])
            if (decision["proposal_digest"] != proposal["digest"] or
                    decision["read_binding"] != proposal["read_binding"] or
                    decision["expires_tick"] > proposal["expires_tick"]):
                raise ValueError("decision_binding")
            if decision["status"] == "approved":
                self._check_binding(c, proposal)
            old = c.execute("SELECT payload,actor FROM decisions WHERE board=? AND id=?",
                            (decision["board_id"], decision["decision_id"])).fetchone()
            if old:
                if old["payload"] == canonical_json(decision) and old["actor"] == canonical_json(actor):
                    return
                raise ValueError("decision_id_conflict")
            c.execute("INSERT INTO decisions(board,id,proposal,payload,actor) VALUES (?,?,?,?,?)",
                      (decision["board_id"], decision["decision_id"], decision["proposal_id"],
                       canonical_json(decision), canonical_json(actor)))

    def inspect_decision(self, board_id, decision_id, actor):
        """Read actual journal payload/consumption for acceptance observation.

        This is not controller evidence selection or a policy-budget bypass.
        No receipt inference, mutation, privileged actor mapping or cross-board
        lookup is performed. JSON decoding gives callers a fresh independent copy.
        """
        _authorize(actor, board_id, "read")
        identifier(decision_id)
        with self._connection() as c:
            row = c.execute("SELECT payload,consumed FROM decisions WHERE board=? AND id=?",
                            (board_id, decision_id)).fetchone()
            if row is None:
                return None
            decision = json.loads(row["payload"])
            if decision["board_id"] != board_id or decision["decision_id"] != decision_id:
                raise ValueError("decision_observation_scope")
            if type(row["consumed"]) is not int or row["consumed"] not in (0, 1):
                raise ValueError("invalid_persisted_consumption")
            return {"decision": decision, "consumed": row["consumed"] == 1}

    def lookup_intent(self, board_id, key, actor):
        _authorize(actor, board_id, "read")
        with self._connection() as c:
            self._board(c, board_id)
            row = c.execute("SELECT receipt FROM intents WHERE board=? AND key=?", (board_id, key)).fetchone()
            return None if row is None else json.loads(row["receipt"])

    def advance_to(self, board_id, tick, actor):
        _authorize(actor, board_id, "advance")
        integer(tick, 0, 96)
        with self._connection(write=True) as c:
            old = self._board(c, board_id)["tick"]
            if tick < old:
                raise ValueError("clock_backwards")
            if tick != old:
                initial = self._snapshot(c, board_id, history=False)
                boundaries = self._clock_boundaries(initial["records"], old, tick)
                # Each crossed relevant instant is an actual logical clock step.
                # Start AND end remain distinct even when final eligibility equals
                # initial eligibility. All steps/epochs/history commit together.
                instants = sorted(set(boundaries) | {tick})
                for instant in instants:
                    before = self._snapshot(c, board_id, history=False)
                    targets = sorted(boundaries.get(instant, set()))
                    for task_id in targets:
                        c.execute("UPDATE epochs SET epoch=epoch+1 WHERE board=? AND task=?",
                                  (board_id, task_id))
                    c.execute("UPDATE boards SET tick=? WHERE id=?", (instant, board_id))
                    after = self._snapshot(c, board_id, history=False)
                    self._append_history(c, board_id, "clock", before, after, "world", actor["label"],
                                         epoch_boundary_tasks=targets)

    @staticmethod
    def _clock_boundaries(records, old_tick, new_tick):
        """Host-owned time predicates over public typed records, not grades.

        Values are task sets at DISTINCT crossed instants. Repeated calls at the
        same tick and unrelated/future events do not advance any task episode.
        A grant must belong to the task's actual assignee and task/project scope;
        availability of a possible delegate matters only under such a grant
        active immediately before OR at the availability boundary.
        """
        tasks = {row["id"]: row for row in records["tasks"]}
        transitions = {}

        def add(instant, task_ids):
            if type(instant) is int and old_tick < instant <= new_tick:
                selected = set(task_ids) & tasks.keys()
                if selected:
                    transitions.setdefault(instant, set()).update(selected)

        def interval_boundaries(row):
            period = row["effective_interval"]
            return period["start_tick"], period["end_tick"]

        def grant_matches(grant, task):
            scope = grant["scope"]
            return (task["assignee_id"] is not None
                    and grant["from_person_id"] == task["assignee_id"]
                    and grant["to_person_id"] != task["assignee_id"]
                    and (scope["kind"], scope["id"]) in
                    (("task", task["id"]), ("project", task["project_id"])))

        def active_beside(grant, instant):
            start, end = interval_boundaries(grant)
            # Integer clock: instant-1 is the left side of the half-open edge.
            return start <= instant - 1 < end or start <= instant < end

        # These are explicit controller/host task time predicates. A dependency's
        # time gating is also relevant to tasks still linked to that dependency.
        def task_and_dependants(task_id):
            return {task_id} | {link["task_id"] for link in records["dependency_links"]
                                if link["dependency_task_id"] == task_id}

        for task in tasks.values():
            related = task_and_dependants(task["id"])
            add(task["not_before_tick"], related)
            window = task["work_window"]
            if window is not None:
                add(window["start_tick"], related)
                add(window["end_tick"], related)

        for row in records["availability"]:
            for instant in interval_boundaries(row):
                affected = set()
                for task in tasks.values():
                    if task["assignee_id"] == row["person_id"]:
                        affected.add(task["id"])
                    elif any(grant["to_person_id"] == row["person_id"]
                             and grant_matches(grant, task) and active_beside(grant, instant)
                             for grant in records["delegations"]):
                        affected.add(task["id"])
                add(instant, affected)

        for grant in records["delegations"]:
            affected = {task["id"] for task in tasks.values() if grant_matches(grant, task)}
            for instant in interval_boundaries(grant):
                add(instant, affected)

        # The supported dependency policy also checks current task-linked
        # documents. Project-only/version-only unrelated rows are not a clock
        # predicate. Typed document task links stay in their own project.
        for document in records["documents"]:
            affected = set()
            for task_id in document["task_ids"]:
                task = tasks.get(task_id)
                if task is not None and task["project_id"] == document["project_id"]:
                    affected.update(task_and_dependants(task_id))
            for instant in interval_boundaries(document):
                add(instant, affected)
        return transitions

    @staticmethod
    def _receipt(proposal, decision, tick, status, reason=None):
        return {"receipt_id": "r-" + digest_json([proposal["board_id"], proposal["proposal_id"], decision["decision_id"]]),
                "board_id": proposal["board_id"], "proposal_id": proposal["proposal_id"],
                "decision_id": decision["decision_id"], "proposal_digest": proposal["digest"],
                "intent_key": proposal["intent"]["intent_key"], "applied_tick": tick, "status": status,
                "committed": status == "applied", "actual_write_set": [], "outbox_event_ids": [],
                "recovered_original_receipt_id": None, "reason_code": reason}

    def apply(self, approved_bundle, actor):
        approved_bundle = deepcopy(approved_bundle)
        closed(approved_bundle, "proposal decision")
        proposal, decision = approved_bundle["proposal"], approved_bundle["decision"]
        validate_proposal(proposal)
        validate_decision(decision)
        board_id = proposal["board_id"]
        _authorize(actor, board_id, "apply")
        with self._connection(write=True) as c:
            tick = self._board(c, board_id)["tick"]
            stored_p = c.execute("SELECT payload FROM proposals WHERE board=? AND id=?",
                                 (board_id, proposal["proposal_id"])).fetchone()
            stored_d = c.execute("SELECT payload,actor,consumed FROM decisions WHERE board=? AND id=?",
                                 (board_id, decision["decision_id"])).fetchone()
            if stored_p is None or stored_d is None:
                return self._receipt(proposal, decision, tick, "not_applied", "missing_journal")
            if stored_p["payload"] != canonical_json(proposal) or stored_d["payload"] != canonical_json(decision):
                return self._receipt(proposal, decision, tick, "conflict", "journal_payload_conflict")
            operator = json.loads(stored_d["actor"])
            _authorize(operator, board_id, "decide")
            if (decision["board_id"] != board_id or decision["proposal_id"] != proposal["proposal_id"] or
                    decision["proposal_digest"] != proposal["digest"] or
                    decision["read_binding"] != proposal["read_binding"] or
                    decision["operator_label"] != operator["label"] or decision["actor_kind"] != operator["kind"]):
                return self._receipt(proposal, decision, tick, "conflict", "decision_binding")
            original = c.execute("SELECT payload,receipt FROM intents WHERE board=? AND key=?",
                                 (board_id, proposal["intent"]["intent_key"])).fetchone()
            if original:
                if original["payload"] == canonical_json(proposal):
                    return json.loads(original["receipt"])  # Exact original, even after expiry/ack loss.
                return self._receipt(proposal, decision, tick, "conflict", "intent_payload_conflict")
            if decision["status"] != "approved":
                return self._receipt(proposal, decision, tick, decision["status"], "decision_not_approved")
            if stored_d["consumed"]:
                return self._receipt(proposal, decision, tick, "not_applied", "decision_consumed")
            later = c.execute("SELECT payload FROM decisions WHERE board=? AND proposal=? AND id<>?",
                              (board_id, proposal["proposal_id"], decision["decision_id"])).fetchall()
            if any(json.loads(row["payload"])["status"] in ("rejected", "expired", "superseded") and
                   json.loads(row["payload"])["decided_tick"] >= decision["decided_tick"] for row in later):
                return self._receipt(proposal, decision, tick, "superseded", "later_terminal_decision")
            if not decision["decided_tick"] <= tick < decision["expires_tick"]:
                return self._receipt(proposal, decision, tick, "expired", "decision_expired")
            try:
                self._check_binding(c, proposal)
                self._check_policy(c, proposal)
            except ValueError as error:
                reason = str(error)
                status = "expired" if reason == "expired" else "stale"
                return self._receipt(proposal, decision, tick, status, reason)
            before = self._snapshot(c, board_id, history=False)
            receipt = self._receipt(proposal, decision, tick, "applied")
            c.execute("UPDATE decisions SET consumed=1 WHERE board=? AND id=? AND consumed=0",
                      (board_id, decision["decision_id"]))
            receipt["actual_write_set"], receipt["outbox_event_ids"] = self._mutate(
                c, board_id, proposal["compiled_write_set"], tick, "agent" if
                any(w.get("actor_role") == "agent" for w in proposal["compiled_write_set"]) else "rules",
                proposal["proposal_id"])
            self._bump_epochs(c, board_id, proposal["compiled_write_set"], before)
            after = self._snapshot(c, board_id, history=False)
            c.execute("INSERT INTO intents VALUES (?,?,?,?)",
                      (board_id, receipt["intent_key"], canonical_json(proposal), canonical_json(receipt)))
            role = "agent" if any(w.get("actor_role") == "agent"
                                       for w in proposal["compiled_write_set"]) else "rules"
            self._append_history(c, board_id, "apply", before, after, role, actor["label"],
                                 proposal=proposal, decision=decision, receipt=receipt,
                                 changes=receipt["actual_write_set"])
            if self.failpoint == "precommit_abort":
                raise PrecommitAbort("injected before commit; recover only after rollback")
            if self.failpoint not in (None, "postcommit_ack_loss"):
                raise ValueError("unknown_failpoint")
        if self.failpoint == "postcommit_ack_loss":
            raise PostcommitAckLoss("commit completed; recover using lookup_intent")
        return receipt

    def _check_policy(self, c, proposal):
        board_id, task_id = proposal["board_id"], proposal["task_id"]
        task = self._record(c, board_id, "tasks", task_id)
        tick = self._board(c, board_id)["tick"]
        if task is None or task["status"] in ("parked", "done"):
            raise ValueError("task_not_actionable")
        if task["wait_reason"] is not None or (task["not_before_tick"] is not None and tick < task["not_before_tick"]):
            raise ValueError("covered_wait")
        records = self._snapshot(c, board_id, history=False)["records"]
        deleting = {w["id"] for w in proposal["compiled_write_set"] if w["op"] == "delete"}
        for action in proposal["action_bundle"]:
            kind = action["action_kind"]
            if kind == "clear_dependency":
                link = self._record(c, board_id, "dependency_links", action["dependency_link_id"])
                dep = self._record(c, board_id, "tasks", action["dependency_task_id"])
                if (link is None or link["task_id"] != task_id or
                        link["dependency_task_id"] != action["dependency_task_id"] or dep is None or dep["status"] != "done"):
                    raise ValueError("unsatisfied_dependency")
            elif kind == "set_ready":
                if task["status"] not in ("todo", "blocked"):
                    raise ValueError("status_not_ready_transition")
                if any(link["task_id"] == task_id and link["id"] not in deleting
                       for link in records["dependency_links"]):
                    raise ValueError("remaining_blocker")
            elif kind == "reassign_to_delegate":
                self._check_delegate(task, action, records, tick)
            elif kind == "request_info":
                for row in records["comments"]:
                    if row["task_id"] != task_id or row["topic"] != action["topic"] or row["origin"] != "arm":
                        continue
                    source = c.execute("SELECT payload FROM proposals WHERE board=? AND id=?",
                                       (board_id, row["source_proposal_id"])).fetchone()
                    if source is None:
                        raise ValueError("missing_comment_provenance")
                    source_epoch = json.loads(source["payload"])["intent"]["episode_epoch"]
                    if source_epoch == proposal["intent"]["episode_epoch"]:
                        raise ValueError("existing_information_request")
        for write in proposal["compiled_write_set"]:
            if write["kind"] == "comments":
                if write["task_id"] != task_id or self._record(c, board_id, "comments", write["id"]) is not None:
                    raise ValueError("comment_scope_or_noop")
            elif write["kind"] == "tasks" and write["id"] != task_id:
                raise ValueError("cross_task_write")

    @staticmethod
    def _check_delegate(task, action, records, tick):
        window = task["work_window"]
        if window is None or tick >= window["end_tick"] or task["assignee_id"] == action["delegate_id"]:
            raise ValueError("delegation_work_window")
        def covers(row):
            interval = row["effective_interval"]
            return interval["start_tick"] <= min(tick, window["start_tick"]) and interval["end_tick"] >= window["end_tick"]
        delegation = next((row for row in records["delegations"] if row["id"] == action["delegation_id"]), None)
        availability = next((row for row in records["availability"] if row["id"] == action["availability_id"]), None)
        if (delegation is None or availability is None or
                delegation["from_person_id"] != task["assignee_id"] or
                delegation["to_person_id"] != action["delegate_id"] or
                (delegation["scope"]["kind"], delegation["scope"]["id"]) not in
                (("task", task["id"]), ("project", task["project_id"])) or not covers(delegation) or
                availability["person_id"] != task["assignee_id"] or availability["available"] or not covers(availability)):
            raise ValueError("delegation_not_effective")
        if not any(row["person_id"] == action["delegate_id"] and row["available"] and covers(row)
                   for row in records["availability"]):
            raise ValueError("delegate_unavailable")
        if any(((row["person_id"] == action["delegate_id"] and not row["available"]) or
                (row["person_id"] == task["assignee_id"] and row["available"])) and
               row["effective_interval"]["start_tick"] < window["end_tick"] and
               row["effective_interval"]["end_tick"] > min(tick, window["start_tick"])
               for row in records["availability"]):
            raise ValueError("conflicting_availability")

    def _mutate(self, c, board_id, writes, tick, origin, proposal_id=None, source_event_id=None):
        changes, event_ids = [], []
        for index, write in enumerate(writes):
            kind, id = write["kind"], write["id"]
            previous = self._record(c, board_id, kind, id)
            field = write.get("field")
            if write["op"] == "delete":
                if previous is None or previous["task_id"] != write["task_id"] or previous["dependency_task_id"] != write["dependency_task_id"]:
                    raise ValueError("delete_scope")
                c.execute("DELETE FROM records WHERE board=? AND kind=? AND id=?", (board_id, kind, id))
                before, after, version = previous, None, previous["version"] + 1
            elif write["op"] == "update":
                if previous is None or previous[field] == write["value"]:
                    raise ValueError("missing_or_noop")
                updated = dict(previous)
                before, after = previous[field], write["value"]
                updated[field], updated["version"] = after, previous["version"] + 1
                self._put(c, board_id, kind, updated)
                version = updated["version"]
            else:
                if previous is not None or (proposal_id is None and source_event_id is None):
                    raise ValueError("comment_insert_scope")
                after = {key: deepcopy(write[key]) for key in ("id", "task_id", "body", "actor_role", "cites", "topic")}
                after.update(version=1, actor_id=None, occurred_tick=tick,
                             origin="arm" if proposal_id is not None else "exogenous",
                             source_event_id=source_event_id, source_proposal_id=proposal_id)
                self._put(c, board_id, kind, after)
                before, version = None, 1
            changes.append({"op": write["op"], "kind": kind, "id": id, "field": field, "before": before, "after": after})
            c.execute("UPDATE boards SET revision=revision+1 WHERE id=?", (board_id,))
            seq = c.execute("INSERT INTO outbox(board,payload) VALUES (?,?)", (board_id, "{}")).lastrowid
            event_id = "e-" + digest_json([board_id, seq])
            payload = {"event_id": event_id, "board_id": board_id, "seq": seq, "entity_kind": kind,
                       "entity_id": id, "entity_version": version, "occurred_tick": tick, "origin": origin,
                       "payload_digest": digest_json(changes[-1])}
            c.execute("UPDATE outbox SET payload=? WHERE seq=?", (canonical_json(payload), seq))
            event_ids.append(event_id)
        validate_graph(self._snapshot(c, board_id, history=False)["records"])
        return changes, event_ids

    @staticmethod
    def _bump_epochs(c, board_id, writes, before):
        # Actual domain transitions only. Comments never alone reopen a blocker.
        affected = set()
        for write in writes:
            if write["kind"] == "tasks":
                affected.add(write["id"])
                affected.update(link["task_id"] for link in before["records"]["dependency_links"]
                                if link["dependency_task_id"] == write["id"])
            elif write["kind"] == "dependency_links":
                affected.add(write["task_id"])
        for task in affected:
            c.execute("UPDATE epochs SET epoch=epoch+1 WHERE board=? AND task=?", (board_id, task))

    def scripted_edit(self, board_id, changes, actor):
        _authorize(actor, board_id, "scripted_edit")
        if actor["kind"] != "scripted":
            raise PermissionError("scripted_actor_required")
        changes = deepcopy(changes)
        validate_writes(changes, scripted=True)
        with self._connection(write=True) as c:
            tick = self._board(c, board_id)["tick"]
            before = self._snapshot(c, board_id, history=False)
            # A content-addressed control ID is persisted, not a person/proposal ID.
            source = "script-" + digest_json([board_id, tick, before["evidence_scope_revision"], changes])
            actual, events = self._mutate(c, board_id, changes, tick, "exogenous", source_event_id=source)
            self._bump_epochs(c, board_id, changes, before)
            self._append_history(c, board_id, "scripted_edit", before,
                                 self._snapshot(c, board_id, history=False), "world", actor["label"],
                                 source_event_id=source, changes=actual, outbox_event_ids=events)
