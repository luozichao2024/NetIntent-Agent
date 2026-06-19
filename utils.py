from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

ROOT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = ROOT_DIR / "config" / "topology.yaml"
LOG_PATH = ROOT_DIR / "logs" / "run_logs.json"


def load_topology(path: str | Path = CONFIG_PATH) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_jsonable(obj: Any) -> Any:
    try:
        json.dumps(obj, ensure_ascii=False)
        return obj
    except TypeError:
        return str(obj)


def append_run_log(record: dict[str, Any], path: str | Path = LOG_PATH) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                data = []
        except json.JSONDecodeError:
            data = []
    else:
        data = []
    data.append(ensure_jsonable(record))
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def is_real_execution_enabled() -> bool:
    return os.getenv("EXECUTE_REAL_COMMANDS", "false").lower() in {"1", "true", "yes", "y"}


def command_allowed(command: str, allowed_prefixes: list[str]) -> bool:
    command = command.strip()
    if not command:
        return False
    first_token = command.split()[0]
    return first_token in set(allowed_prefixes)
