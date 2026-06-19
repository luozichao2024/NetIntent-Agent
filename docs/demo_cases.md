# 稳定演示用例

本文档只覆盖当前仓库已经实现、并且可以稳定复现的演示场景。

推荐运行方式：

```bash
python main.py --scenario access
python main.py --scenario latency
python main.py --input "当前链路延迟过高，请自动切换备用路径。"
```

默认是 mock 模式，不依赖 Mininet 也能完整跑通闭环。

## 用例 1：访问控制

输入：

```text
禁止学生网段访问管理服务器，但允许教师网段访问。
```

Intent JSON：

```json
{
  "intent_type": "access_control",
  "source": "student_host",
  "destination": "admin_server",
  "action": "deny",
  "constraint": null
}
```

Planner JSON：

```json
{
  "policy_type": "acl",
  "target": "student_to_admin",
  "method": "iptables",
  "command": "iptables -A FORWARD -s 10.0.0.1 -d 10.0.0.10 -j DROP",
  "expected_result": "student_host cannot reach admin_server; teacher_host can reach admin_server",
  "reason": "access control requirement"
}
```

Verifier 结果：

```json
{
  "verify_status": "success",
  "test_tool": "ping",
  "expected": "student_host unreachable; teacher_host reachable",
  "actual": "student_host unreachable; teacher_host reachable",
  "need_replan": false,
  "feedback": null
}
```

最终状态：`success`

演示价值：最稳的正向闭环，适合开场先展示。

## 用例 2：低延迟保障 + 自愈重规划

输入：

```text
保证客户端到服务器的延迟低于50ms。
```

Intent JSON：

```json
{
  "intent_type": "latency_guarantee",
  "source": "client_host",
  "destination": "server",
  "action": "guarantee",
  "constraint": {
    "latency_ms": 50
  }
}
```

第一次 Planner JSON：

```json
{
  "policy_type": "latency_control",
  "target": "client_to_server",
  "method": "ovs",
  "command": "ovs-ofctl add-flow s3 priority=10,ip,nw_src=10.0.1.1,nw_dst=10.0.1.10,actions=output:primary",
  "expected_result": "client_host reaches server with latency < 50ms",
  "reason": "latency guarantee requirement"
}
```

第一次 Verifier 结果：

```json
{
  "verify_status": "failed",
  "test_tool": "ping",
  "expected": "latency < 50ms",
  "actual": "latency = 120ms",
  "need_replan": true,
  "feedback": "current path latency is too high, please switch to backup path"
}
```

重规划后 Planner JSON：

```json
{
  "policy_type": "reroute",
  "target": "client_to_server",
  "method": "ovs",
  "command": "ovs-ofctl add-flow s3 priority=20,ip,nw_src=10.0.1.1,nw_dst=10.0.1.10,actions=output:backup",
  "expected_result": "client_host reaches server with latency < 50ms",
  "reason": "current path latency is too high, please switch to backup path"
}
```

第二次 Verifier 结果：

```json
{
  "verify_status": "success",
  "test_tool": "ping",
  "expected": "backup path latency < 50ms",
  "actual": "backup path latency = 35ms",
  "need_replan": false,
  "feedback": null
}
```

最终状态：`success`

演示价值：第一次失败、第二次成功是预期行为，用来体现闭环重规划。

## 用例 3：故障恢复 / 备用路径切换

输入：

```text
当前链路延迟过高，请自动切换备用路径。
```

Intent JSON：

```json
{
  "intent_type": "failure_recovery",
  "source": "client_host",
  "destination": "server",
  "action": "reroute",
  "constraint": {
    "latency_ms": 50
  }
}
```

Planner JSON：

```json
{
  "policy_type": "reroute",
  "target": "client_to_server",
  "method": "ovs",
  "command": "ovs-ofctl add-flow s3 priority=20,ip,nw_src=10.0.1.1,nw_dst=10.0.1.10,actions=output:backup",
  "expected_result": "client_host reaches server with latency < 50ms",
  "reason": "previous path latency exceeded threshold"
}
```

Verifier 结果：

```json
{
  "verify_status": "success",
  "test_tool": "ping",
  "expected": "backup path latency < 50ms",
  "actual": "backup path latency = 35ms",
  "need_replan": false,
  "feedback": null
}
```

最终状态：`success`

演示价值：可以直接展示“故障感知 -> 备用路径 -> 验证成功”的完整链路。

## 安全降级样例

输入：

```text
请限制访客访问数据库。
```

Intent JSON：

```json
{
  "intent_type": "unknown",
  "source": null,
  "destination": null,
  "action": "unknown",
  "constraint": null
}
```

Planner JSON：

```json
{
  "policy_type": "noop",
  "target": "unknown",
  "method": "none",
  "command": "",
  "expected_result": "unsupported intent",
  "reason": "unsupported or unknown intent"
}
```

这个样例用于说明：系统不会为未支持的需求编造主机、命令或策略。
