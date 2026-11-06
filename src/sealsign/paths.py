"""Локальные пути: разрешение без создания файлов и каталогов."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimePaths:
    data: Path
    artifacts: Path

    @classmethod
    def from_env(cls) -> "RuntimePaths":
        return cls(
            data=Path(os.environ.get("SEALSIGN_DATA_DIR", "data")).expanduser().resolve(),
            artifacts=Path(os.environ.get("SEALSIGN_ARTIFACTS_DIR", "artifacts"))
            .expanduser()
            .resolve(),
        )
