"""Tests for the Phase 1 database layer."""

from pathlib import Path

import pytest
from alembic.command import upgrade as alembic_upgrade
from alembic.config import Config
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from rootguard.db.engine import get_engine
from rootguard.db.models import Decision, Outcome, Record, Run

REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_SCRIPT = (
    REPO_ROOT / "src" / "rootguard" / "db" / "migrations" / "versions"
    / "0001_initial.py"
)


def _alembic_config(db_file: Path) -> Config:
    cfg = Config(str(REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_file}")
    return cfg


def _upgraded_engine(db_file: Path):
    alembic_upgrade(_alembic_config(db_file), "head")
    return get_engine(db_file)


def _table_names(engine) -> set:
    with engine.connect() as conn:
        rows = conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).all()
    return {row[0] for row in rows}


def test_alembic_upgrade_head_on_fresh_db(tmp_path: Path) -> None:
    db_file = tmp_path / "fresh.db"
    assert not db_file.exists()
    engine = _upgraded_engine(db_file)
    assert {"records", "decisions", "outcomes", "runs"} <= _table_names(engine)


def _make_run(session: Session) -> Run:
    run = Run(kind="train", seed=42, config_json={}, metrics_json={})
    session.add(run)
    session.flush()
    return run


def test_records_round_trip(tmp_path: Path) -> None:
    engine = _upgraded_engine(tmp_path / "roundtrip.db")
    with Session(engine) as session:
        run = _make_run(session)
        record = Record(
            family_id="fam-001",
            user_request="list files in the sandbox",
            source="user_direct",
            injected_text=None,
            proposed_action="ls",
            reversibility="reversible",
            scope="single_folder",
            privilege="user",
            label="safe",
            reasoning="",
            provenance="seed",
            split="train",
            reviewed=False,
        )
        session.add(record)
        decision = Decision(
            run_id=run.id,
            request="list files in the sandbox",
            proposed_action="ls",
            source="user_direct",
            features_json={"similarity": 0.9},
            score=0.1,
            decision="allow",
            reason="low risk",
            mode="live",
            model_version="test",
        )
        session.add(decision)
        null_score = Decision(
            run_id=None,
            request="unscored",
            proposed_action="ls",
            source="user_direct",
            features_json={},
            score=None,
            decision="block",
            reason="fail closed without score",
            mode="live",
            model_version="test",
        )
        session.add(null_score)
        session.flush()
        outcome = Outcome(decision_id=decision.id, outcome="correct", note=None)
        session.add(outcome)
        session.commit()

        assert session.get(Record, record.id).user_request == (
            "list files in the sandbox"
        )
        assert session.get(Record, record.id).reviewed is False
        assert session.get(Decision, decision.id).score == 0.1
        assert session.get(Decision, null_score.id).score is None
        assert session.get(Decision, null_score.id).run_id is None
        assert session.get(Outcome, outcome.id).outcome == "correct"
        finished = session.get(Run, run.id)
        assert finished.kind == "train" and finished.seed == 42
        assert finished.started_at is not None


def _record_values(**overrides) -> dict:
    values = {
        "family_id": "fam-001",
        "user_request": "req",
        "source": "user_direct",
        "injected_text": None,
        "proposed_action": "ls",
        "reversibility": "reversible",
        "scope": "single_folder",
        "privilege": "user",
        "label": "safe",
        "reasoning": "",
        "provenance": "seed",
        "split": "train",
        "reviewed": 0,
    }
    values.update(overrides)
    return values


def _decision_values(**overrides) -> dict:
    values = {
        "run_id": None,
        "request": "req",
        "proposed_action": "ls",
        "source": "user_direct",
        "features_json": "{}",
        "score": 0.1,
        "decision": "allow",
        "reason": "",
        "mode": "live",
        "model_version": "test",
    }
    values.update(overrides)
    return values


ENUM_VIOLATIONS = [
    ("records", _record_values(source="bogus_source")),
    ("records", _record_values(reversibility="bogus")),
    ("records", _record_values(scope="bogus")),
    ("records", _record_values(privilege="bogus")),
    ("records", _record_values(label="bogus")),
    ("records", _record_values(provenance="bogus")),
    ("records", _record_values(split="bogus")),
    ("decisions", _decision_values(source="bogus_source")),
    ("decisions", _decision_values(decision="bogus")),
    ("decisions", _decision_values(mode="bogus")),
    ("decisions", _decision_values(score=1.5)),
    ("runs", {"kind": "bogus", "seed": 42, "config_json": "{}", "metrics_json": "{}"}),
]


@pytest.mark.parametrize("table,values", ENUM_VIOLATIONS)
def test_invalid_enum_values_rejected_by_db(
    tmp_path: Path, table: str, values: dict
) -> None:
    engine = _upgraded_engine(tmp_path / "checks.db")
    columns = ", ".join(values.keys())
    placeholders = ", ".join("?" * len(values))
    with engine.begin() as conn:
        with pytest.raises(IntegrityError):
            conn.exec_driver_sql(
                f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                tuple(values.values()),
            )


def test_invalid_outcome_rejected_by_db(tmp_path: Path) -> None:
    engine = _upgraded_engine(tmp_path / "outcome.db")
    with Session(engine) as session:
        decision = Decision(**_decision_values_for_orm())
        session.add(decision)
        session.commit()
        decision_id = decision.id
    with engine.begin() as conn:
        with pytest.raises(IntegrityError):
            conn.exec_driver_sql(
                "INSERT INTO outcomes (decision_id, outcome) VALUES (?, ?)",
                (decision_id, "bogus_outcome"),
            )


def _decision_values_for_orm() -> dict:
    values = _decision_values()
    values["features_json"] = {"similarity": 0.5}
    return values


def test_journal_mode_is_wal(tmp_path: Path) -> None:
    engine = get_engine(tmp_path / "wal.db")
    with engine.connect() as conn:
        mode = conn.exec_driver_sql("PRAGMA journal_mode").scalar()
    assert mode.lower() == "wal"


def test_migration_contains_enum_checks() -> None:
    source = MIGRATION_SCRIPT.read_text()
    for value in (
        "user_direct", "file_content", "web_content", "tool_output",
        "pr_content", "agent_internal", "reversible", "irreversible",
        "single_file", "single_folder", "multi_file", "single_process",
        "system_wide", "user", "root", "safe", "risky", "seed", "nl2bash",
        "nl2bash_mismatch", "injection_dataset", "generated", "live_log",
        "train", "heldout", "allow", "confirm", "block", "undefended",
        "defended", "live", "correct", "false_positive", "miss", "unknown",
        "eval",
    ):
        assert f"'{value}'" in source, f"{value} missing from migration"
    assert "CHECK" in source.upper()
