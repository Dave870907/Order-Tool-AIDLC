import json
from pathlib import Path
from typing import Any, Optional


class FileStore:
    def __init__(self, data_dir: str):
        self._dir = Path(data_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self._dir / f"{key}.json"

    def get(self, key: str) -> Optional[Any]:
        path = self._path(key)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def set(self, key: str, value: Any) -> None:
        path = self._path(key)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, indent=2)

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()
