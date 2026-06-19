from __future__ import annotations

from typing import Optional


HOST_ALIASES = {
    "student_host": "stu",
    "teacher_host": "tea",
    "admin_server": "admin",
    "client_host": "cli",
    "server": "ser",
}

DEFAULT_HOST_IPS = {
    "student_host": "10.0.0.1",
    "teacher_host": "10.0.0.2",
    "admin_server": "10.0.0.10",
    "client_host": "10.0.1.1",
    "server": "10.0.1.10",
}

TARGET_ALIASES = {
    "student_host": "student",
    "teacher_host": "teacher",
    "admin_server": "admin",
    "client_host": "client",
    "server": "server",
}


def _host_ip(topology_json: dict, host: str) -> str:
    hosts = topology_json.get("hosts", {})
    host_key = host if host in hosts else HOST_ALIASES.get(host, host)
    if host_key in hosts and isinstance(hosts[host_key], dict):
        return hosts[host_key].get("ip", DEFAULT_HOST_IPS.get(host, ""))
    return DEFAULT_HOST_IPS.get(host, "")


def _target(source: str, destination: str) -> str:
    src = TARGET_ALIASES.get(source, source)
    dst = TARGET_ALIASES.get(destination, destination)
    return f"{src}_to_{dst}"


def _latency_threshold(intent_json: dict) -> int:
    constraint = intent_json.get("constraint") or {}
    return int(constraint.get("latency_ms", 50))


def plan_policy(intent_json: dict, topology_json: dict, feedback_json: Optional[dict] = None) -> dict:
    """统一接口：Intent JSON + topology + optional feedback -> Policy JSON。"""
    intent_type = intent_json.get("intent_type")

    if intent_type == "access_control":
        src = intent_json["source"]
        dst = intent_json["destination"]
        src_ip = _host_ip(topology_json, src)
        dst_ip = _host_ip(topology_json, dst)
        return {
            "policy_type": "acl",
            "target": _target(src, dst),
            "method": "iptables",
            "command": f"iptables -A FORWARD -s {src_ip} -d {dst_ip} -j DROP",
            "expected_result": f"{src} cannot reach {dst}; teacher_host can reach {dst}",
            "reason": "access control requirement",
        }

    if intent_type in {"latency_guarantee", "failure_recovery"}:
        src = intent_json.get("source") or "client_host"
        dst = intent_json.get("destination") or "server"
        src_ip = _host_ip(topology_json, src)
        dst_ip = _host_ip(topology_json, dst)
        threshold = _latency_threshold(intent_json)
        need_replan = intent_type == "failure_recovery" or bool(feedback_json and feedback_json.get("need_replan"))
        if need_replan:
            return {
                "policy_type": "reroute",
                "target": _target(src, dst),
                "method": "ovs",
                "command": f"ovs-ofctl add-flow s3 priority=20,ip,nw_src={src_ip},nw_dst={dst_ip},actions=output:backup",
                "expected_result": f"{src} reaches {dst} with latency < {threshold}ms",
                "reason": (feedback_json or {}).get("feedback", "previous path latency exceeded threshold"),
            }
        return {
            "policy_type": "latency_control",
            "target": _target(src, dst),
            "method": "ovs",
            "command": f"ovs-ofctl add-flow s3 priority=10,ip,nw_src={src_ip},nw_dst={dst_ip},actions=output:primary",
            "expected_result": f"{src} reaches {dst} with latency < {threshold}ms",
            "reason": "latency guarantee requirement",
        }

    return {
        "policy_type": "noop",
        "target": "unknown",
        "method": "none",
        "command": "",
        "expected_result": "unsupported intent",
        "reason": "unsupported or unknown intent",
    }
