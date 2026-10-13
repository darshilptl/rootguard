"""SQLAlchemy models for the RootGuard defense layer database."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    false,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

SOURCE_VALUES = (
    "user_direct",
    "file_content",
    "web_content",
    "tool_output",
    "pr_content",
    "agent_internal",
)
REVERSIBILITY_VALUES = ("reversible", "irreversible")
SCOPE_VALUES = (
    "single_file",
    "single_folder",
    "multi_file",
    "single_process",
    "system_wide",
)
PRIVILEGE_VALUES = ("user", "root")
LABEL_VALUES = ("safe", "risky")
PROVENANCE_VALUES = (
    "seed",
    "nl2bash",
    "nl2bash_mismatch",
    "injection_dataset",
    "generated",
    "live_log",
)
SPLIT_VALUES = ("train", "heldout")
DECISION_VALUES = ("allow", "confirm", "block")
MODE_VALUES = ("undefended", "defended", "live")
OUTCOME_VALUES = ("correct", "false_positive", "miss", "unknown")
KIND_VALUES = ("train", "eval")


def _enum(*values: str, name: str) -> Enum:
    return Enum(*values, name=name, create_constraint=True, validate_strings=True)


class Base(DeclarativeBase):
    pass


class Record(Base):
    __tablename__ = "records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    family_id: Mapped[str] = mapped_column(String, nullable=False)
    user_request: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(
        _enum(*SOURCE_VALUES, name="record_source"), nullable=False
    )
    injected_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proposed_action: Mapped[str] = mapped_column(Text, nullable=False)
    reversibility: Mapped[str] = mapped_column(
        _enum(*REVERSIBILITY_VALUES, name="record_reversibility"), nullable=False
    )
    scope: Mapped[str] = mapped_column(
        _enum(*SCOPE_VALUES, name="record_scope"), nullable=False
    )
    privilege: Mapped[str] = mapped_column(
        _enum(*PRIVILEGE_VALUES, name="record_privilege"), nullable=False
    )
    label: Mapped[str] = mapped_column(
        _enum(*LABEL_VALUES, name="record_label"), nullable=False
    )
    reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")
    provenance: Mapped[str] = mapped_column(
        _enum(*PROVENANCE_VALUES, name="record_provenance"), nullable=False
    )
    split: Mapped[str] = mapped_column(
        _enum(*SPLIT_VALUES, name="record_split"), nullable=False
    )
    reviewed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(
        _enum(*KIND_VALUES, name="run_kind"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    config_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    metrics_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Decision(Base):
    __tablename__ = "decisions"
    __table_args__ = (
        CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 1)",
            name="decision_score_range",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    run_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("runs.id"), nullable=True
    )
    request: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_action: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(
        _enum(*SOURCE_VALUES, name="decision_source"), nullable=False
    )
    features_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    decision: Mapped[str] = mapped_column(
        _enum(*DECISION_VALUES, name="decision_decision"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    mode: Mapped[str] = mapped_column(
        _enum(*MODE_VALUES, name="decision_mode"), nullable=False
    )
    model_version: Mapped[str] = mapped_column(String, nullable=False)


class Outcome(Base):
    __tablename__ = "outcomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_id: Mapped[int] = mapped_column(
        ForeignKey("decisions.id", ondelete="RESTRICT"), nullable=False
    )
    outcome: Mapped[str] = mapped_column(
        _enum(*OUTCOME_VALUES, name="outcome_outcome"), nullable=False
    )
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
