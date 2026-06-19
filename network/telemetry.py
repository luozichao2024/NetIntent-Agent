from __future__ import annotations

import re
import subprocess

from network.network_control import run_latency_test
from utils import is_real_execution_enabled, load_topology


def _mininet_name(host: str) -> str:
    topology = load_topology()
    hosts = topology.get("hosts", {})
    if host not in hosts:
        return host
    return hosts[host].get("mininet_name", host)


def get_host_info(host_name: str) -> str:
    if not is_real_execution_enabled():
        return f"mock host info for {host_name}"

    try:
        from network.mininet_topo import get_net

        net = get_net()
        if not net:
            return ""
        host = net.get(_mininet_name(host_name))
        return host.cmd("ip addr")
    except Exception as exc:
        return f"failed to get host info: {exc}"


def get_link_status(interface: str) -> str:
    if not is_real_execution_enabled():
        return f"mock link status for {interface}: UP"
    return subprocess.getoutput(f"ip link show {interface}")


def get_average_rtt(source: str, destination: str) -> float | None:
    result = run_latency_test(source, destination)
    if result.get("status") != "success":
        return None

    output = result.get("output", "")

    # Real ping output: rtt min/avg/max/mdev = 1.1/2.2/3.3/0.1 ms
    match = re.search(r"=\s*([\d.]+)/([\d.]+)/", output)
    if match:
        return float(match.group(2))

    # Mock output: avg = 35ms
    mock_match = re.search(r"avg\s*=\s*([\d.]+)\s*ms", output)
    if mock_match:
        return float(mock_match.group(1))

    return None
