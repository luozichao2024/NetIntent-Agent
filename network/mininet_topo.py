from __future__ import annotations

NET = None


def start_mininet_topology():
    """Start a fixed Mininet topology.

    Mininet imports are kept inside this function so that the project can still
    run in mock mode on Windows or machines without Mininet installed.
    """
    global NET

    if NET is not None:
        return NET

    try:
        from mininet.net import Mininet
        from mininet.node import OVSSwitch
        from mininet.link import TCLink
    except ImportError as exc:
        raise RuntimeError(
            "Mininet is not installed. Run this function in a Linux/Mininet environment, "
            "or keep EXECUTE_REAL_COMMANDS=false for mock mode."
        ) from exc

    net = Mininet(switch=OVSSwitch, link=TCLink, controller=None)

    # Short Mininet host names avoid Linux interface-name length issues.
    stu = net.addHost("stu", ip="10.0.0.1/24")
    tea = net.addHost("tea", ip="10.0.0.2/24")
    admin = net.addHost("admin", ip="10.0.0.10/24")
    cli = net.addHost("cli", ip="10.0.1.1/24")
    ser = net.addHost("ser", ip="10.0.1.10/24")

    s1 = net.addSwitch("s1")
    s2 = net.addSwitch("s2")
    s3 = net.addSwitch("s3")
    s4 = net.addSwitch("s4")
    s5 = net.addSwitch("s5")

    # Access-control scenario.
    net.addLink(stu, s1)
    net.addLink(tea, s1)
    net.addLink(s1, s2)
    net.addLink(s2, admin)

    # Latency/self-healing scenario: primary path s3-s4 and backup path s3-s5-s4.
    net.addLink(cli, s3)
    net.addLink(s3, s4)
    net.addLink(s4, ser)
    net.addLink(s3, s5)
    net.addLink(s5, s4)

    net.start()

    # Simple L2 forwarding for stable MVP connectivity.
    for sw in net.switches:
        sw.cmd(f"ovs-ofctl add-flow {sw.name} actions=normal")

    NET = net
    return NET


def stop_mininet_topology() -> None:
    """Stop the running Mininet topology if it exists."""
    global NET
    if NET is not None:
        NET.stop()
        NET = None


def get_net():
    """Return the current Mininet object, or None if the topology is not started."""
    return NET
