from __future__ import annotations


def verify_policy(intent_json: dict, policy_json: dict) -> dict:
    """统一接口：验证策略是否满足意图。

    Default implementation uses stable mock verification so the full pipeline can
    run without Mininet. Member2 can later replace the internal telemetry logic
    while keeping this function signature and return fields unchanged.
    """
    intent_type = intent_json.get("intent_type")

    if intent_type == "access_control":
        return {
            "verify_status": "success",
            "test_tool": "ping",
            "expected": "student_host unreachable; teacher_host reachable",
            "actual": "student_host unreachable; teacher_host reachable",
            "need_replan": False,
            "feedback": None,
        }

    if intent_type == "latency_guarantee":
        threshold = (intent_json.get("constraint") or {}).get("latency_ms", 50)
        if policy_json.get("policy_type") in {"low_latency_path", "latency_control"}:
            return {
                "verify_status": "failed",
                "test_tool": "ping",
                "expected": f"latency < {threshold}ms",
                "actual": "latency = 120ms",
                "need_replan": True,
                "feedback": "current path latency is too high, please switch to backup path",
            }
        return {
            "verify_status": "success",
            "test_tool": "ping",
            "expected": f"latency < {threshold}ms",
            "actual": "latency = 35ms",
            "need_replan": False,
            "feedback": None,
        }

    if intent_type == "failure_recovery":
        threshold = (intent_json.get("constraint") or {}).get("latency_ms", 50)
        if policy_json.get("policy_type") == "reroute":
            return {
                "verify_status": "success",
                "test_tool": "ping",
                "expected": f"backup path latency < {threshold}ms",
                "actual": "backup path latency = 35ms",
                "need_replan": False,
                "feedback": None,
            }
        return {
            "verify_status": "failed",
            "test_tool": "ping",
            "expected": "traffic switched to backup path",
            "actual": "traffic still uses previous path",
            "need_replan": True,
            "feedback": "previous path latency exceeded threshold",
        }

    return {
        "verify_status": "failed",
        "test_tool": "none",
        "expected": "supported intent",
        "actual": "unsupported intent",
        "need_replan": False,
        "feedback": "unsupported intent type",
    }
