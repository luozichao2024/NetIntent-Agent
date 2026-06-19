from __future__ import annotations

import re


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def parse_intent(user_input: str) -> dict:
    """统一接口：自然语言意图 -> JSON。

    成员3后续可以替换本函数内部实现，例如接入LLM或LangChain；函数签名和返回字段保持不变。
    """
    text = user_input.strip().lower()
    latency_match = re.search(r"(\d+)\s*ms", text)
    latency_ms = int(latency_match.group(1)) if latency_match else 50

    if _contains_any(text, ["备用路径", "切换", "重规划", "重新规划", "故障", "自愈", "恢复", "replan", "reroute"]):
        return {
            "intent_type": "failure_recovery",
            "source": "client_host",
            "destination": "server",
            "action": "reroute",
            "constraint": {"latency_ms": latency_ms},
        }

    if _contains_any(text, ["禁止", "阻止", "block", "deny", "不可访问", "访问控制"]):
        return {
            "intent_type": "access_control",
            "source": "student_host",
            "destination": "admin_server",
            "action": "deny",
            "constraint": None,
        }

    if _contains_any(text, ["延迟", "时延", "latency", "低于", "小于", "低延迟", "保证"]):
        return {
            "intent_type": "latency_guarantee",
            "source": "client_host",
            "destination": "server",
            "action": "guarantee",
            "constraint": {"latency_ms": latency_ms},
        }

    return {
        "intent_type": "unknown",
        "source": None,
        "destination": None,
        "action": "unknown",
        "constraint": None,
    }
