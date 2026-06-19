from __future__ import annotations

from network.network_control import run_safe_command


def execute_policy(policy_json: dict) -> dict:
    command = policy_json.get("command", "")
    result = run_safe_command(command)
    return {
        "execute_status": result["status"],
        "executed_command": result["command"],
        "message": result.get("output") or result.get("error"),
        "raw_result": result,
    }
