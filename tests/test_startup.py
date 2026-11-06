"""Проверки автономности старта и отсутствия побочных действий."""

import os
import subprocess
import sys

import pytest

from sealsign.paths import RuntimePaths


@pytest.mark.parametrize("args", [["--help"], ["--version"], []])
def test_cli_without_weights_or_writable_workdir(tmp_path, args):
    result = subprocess.run(
        [sys.executable, "-m", "sealsign", *args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "sealsign" in result.stdout.lower()
    assert not list(tmp_path.iterdir())


def test_import_does_not_load_ml_or_create_files(tmp_path):
    code = (
        "import sys, sealsign, sealsign.cli, sealsign.paths; "
        "assert not {'torch', 'ultralytics', 'fastapi', 'streamlit'} & sys.modules.keys()"
    )
    subprocess.run([sys.executable, "-c", code], cwd=tmp_path, check=True)
    assert not list(tmp_path.iterdir())


def test_paths_respect_external_storage_without_creating_it(tmp_path, monkeypatch):
    monkeypatch.setenv("SEALSIGN_DATA_DIR", str(tmp_path / "external data"))
    monkeypatch.setenv("SEALSIGN_ARTIFACTS_DIR", str(tmp_path / "external artifacts"))
    paths = RuntimePaths.from_env()
    assert paths.data == tmp_path / "external data"
    assert paths.artifacts == tmp_path / "external artifacts"
    assert not paths.data.exists()
    assert not paths.artifacts.exists()


def test_invalid_option_fails(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "sealsign", "--log-level", "INVALID"],
        cwd=tmp_path,
        capture_output=True,
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    assert result.returncode == 2
