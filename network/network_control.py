from __future__ import annotations

import subprocess

from utils import command_allowed, is_real_execution_enabled, load_topology


def _host_ip(host: str) -> str:
    topology = load_topology()
    hosts = topology.get("hosts", {})
    if host not in hosts:
        raise KeyError(f"Unknown host in topology: {host}")
    return hosts[host]["ip"]


def _mininet_name(host: str) -> str:
    topology = load_topology()
    hosts = topology.get("hosts", {})
    if host not in hosts:
        return host
    return hosts[host].get("mininet_name", host)


def _get_net():
    # Import lazily so mock mode works on machines without Mininet.
    from network.mininet_topo import get_net

    return get_net()


def run_safe_command(command: str) -> dict:
    """Run a command only if it is whitelisted and real execution is enabled.

    In default mock mode this function only returns the command that would be run.
    """
    topology = load_topology()
    allowed = topology.get("allowed_command_prefixes", [])

    if not command:
        return {"status": "success", "command": command, "output": "noop", "error": None}

    if not command_allowed(command, allowed):
        return {
            "status": "failed",
            "command": command,
            "output": None,
            "error": "command is not in whitelist",
        }

    if not is_real_execution_enabled():
        return {
            "status": "success",
            "command": command,
            "output": "mock execution; set EXECUTE_REAL_COMMANDS=true to run",
            "error": None,
        }

    try:
        completed = subprocess.run(
            command,
            shell=True,
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        status = "success" if completed.returncode == 0 else "failed"
        return {
            "status": status,
            "command": command,
            "output": completed.stdout.strip(),
            "error": completed.stderr.strip() or None,
        }
    except Exception as exc:
        return {"status": "failed", "command": command, "output": None, "error": str(exc)}


def start_topology() -> None:
    if not is_real_execution_enabled():
        return None
    from network.mininet_topo import start_mininet_topology

    start_mininet_topology()
    return None


def stop_topology() -> None:
    if not is_real_execution_enabled():
        return None
    from network.mininet_topo import stop_mininet_topology

    stop_mininet_topology()
    return None


def apply_acl_block(source: str, destination: str) -> dict:
    src_ip = _host_ip(source)
    dst_ip = _host_ip(destination)
    return run_safe_command(f"iptables -A FORWARD -s {src_ip} -d {dst_ip} -j DROP")


def remove_acl_block(source: str, destination: str) -> dict:
    src_ip = _host_ip(source)
    dst_ip = _host_ip(destination)
    return run_safe_command(f"iptables -D FORWARD -s {src_ip} -d {dst_ip} -j DROP")


def set_link_delay(link_name: str, delay_ms: int) -> dict:
    return run_safe_command(f"tc qdisc replace dev {link_name} root netem delay {delay_ms}ms")


def set_link_down(link_name: str) -> dict:
    return run_safe_command(f"mn --link {link_name} down")


def set_link_up(link_name: str) -> dict:
    return run_safe_command(f"mn --link {link_name} up")


def run_ping(source: str, destination: str) -> dict:
    """Run ping between two topology host names.

    In mock mode, returns a deterministic mock result. In real mode, it uses the
    running Mininet topology and maps standard host names to short Mininet names.
    """
    dst_ip = _host_ip(destination)
    command = f"ping -c 4 {dst_ip}"

    if not is_real_execution_enabled():
        return {
            "status": "success",
            "command": command,
            "output": f"mock ping from {source} to {destination}",
            "error": None,
        }

    try:
        net = _get_net()
        if net is None:
            return {"status": "failed", "command": command, "output": None, "error": "Mininet topology is not started"}
        src = net.get(_mininet_name(source))
        output = src.cmd(command)
        return {"status": "success", "command": command, "output": output, "error": None}
    except Exception as exc:
        return {"status": "failed", "command": command, "output": None, "error": str(exc)}


def run_latency_test(source: str, destination: str) -> dict:
    dst_ip = _host_ip(destination)
    command = f"ping -c 10 {dst_ip}"

    if not is_real_execution_enabled():
        return {
            "status": "success",
            "command": command,
            "output": f"mock latency from {source} to {destination}: avg = 35ms",
            "error": None,
        }

    try:
        net = _get_net()
        if net is None:
            return {"status": "failed", "command": command, "output": None, "error": "Mininet topology is not started"}
        src = net.get(_mininet_name(source))
        output = src.cmd(command)
        return {"status": "success", "command": command, "output": output, "error": None}
    except Exception as exc:
        return {"status": "failed", "command": command, "output": None, "error": str(exc)}
