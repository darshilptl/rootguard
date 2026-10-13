"""Central configuration for the RootGuard defense layer."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RootGuardConfig:
    hf_home: Path = Path("./models/hf")
    seed: int = 42
    db_path: Path = Path("data/rootguard.db")


def load_config() -> RootGuardConfig:
    return RootGuardConfig()
