"""Smoke tests for the Phase 0 scaffold."""

from pathlib import Path

from typer.testing import CliRunner

from rootguard.cli.app import app
from rootguard.config import load_config

runner = CliRunner()


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() != ""


def test_config_defaults() -> None:
    config = load_config()
    assert config.hf_home == Path("./models/hf")
    assert config.seed == 42
