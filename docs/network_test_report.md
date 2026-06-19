# Network Test Report

## 1. 测试目的

本文档用于说明 NetIntent-Agent 项目的网络模块设计、网络控制命令设计以及当前测试状态。

本项目的目标不是只做自然语言问答系统，而是构建一个能够面向网络运维场景完成“意图解析、策略生成、命令生成、结果验证和失败重规划”的闭环系统。因此，网络模块主要承担以下作用：

1. 提供固定的小型网络拓扑。
2. 为访问控制场景生成可执行的网络控制命令。
3. 为低延迟保障和链路自愈场景生成路径控制或流表调整命令。
4. 为 Verifier Agent 提供可达性、延迟和状态验证依据。
5. 为后续迁移到 Linux / Mininet / Open vSwitch 环境提供接口基础。

---

## 2. 网络拓扑设计

当前项目采用固定的小型实验网拓扑，主要包含两类场景：访问控制场景和低延迟 / 自愈场景。

### 2.1 访问控制场景拓扑

```text
student_host ---- s1 ---- s2 ---- admin_server
teacher_host ----/
```

该场景包含：

| 节点             | 含义     | IP 地址       |
| -------------- | ------ | ----------- |
| `student_host` | 学生网段主机 | `10.0.0.1`  |
| `teacher_host` | 教师网段主机 | `10.0.0.2`  |
| `admin_server` | 管理服务器  | `10.0.0.10` |
| `s1`, `s2`     | 交换节点   | -           |

访问控制场景的目标是：

```text
阻断 student_host → admin_server
保持 teacher_host → admin_server 可达
```

该场景用于展示系统从自然语言访问控制需求自动生成 ACL 策略，并完成验证的能力。

---

### 2.2 低延迟与自愈场景拓扑

```text
client_host ---- s3 ---- s4 ---- server
               \       /
                -- s5 --
```

该场景包含：

| 节点            | 含义       | IP 地址       |
| ------------- | -------- | ----------- |
| `client_host` | 客户端主机    | `10.0.1.1`  |
| `server`      | 服务端主机    | `10.0.1.10` |
| `s3`, `s4`    | 主路径交换节点  | -           |
| `s5`          | 备用路径交换节点 | -           |

该场景的目标是：

```text
保证 client_host 到 server 的延迟低于 50ms。
```

当初始路径延迟过高时，Verifier Agent 返回失败结果和反馈信息，Planner Agent 根据反馈生成备用路径策略，实现重规划与自愈。

---

## 3. 主机命名与 IP 设计

系统内部统一使用以下主机名和 IP 地址：

| 标准主机名          | Mininet 简写名 | IP 地址       |
| -------------- | ----------- | ----------- |
| `student_host` | `stu`       | `10.0.0.1`  |
| `teacher_host` | `tea`       | `10.0.0.2`  |
| `admin_server` | `admin`     | `10.0.0.10` |
| `client_host`  | `cli`       | `10.0.1.1`  |
| `server`       | `ser`       | `10.0.1.10` |

其中，系统中的 Intent Agent、Planner Agent 和 Pipeline 使用标准主机名；Mininet 环境中可以使用简写名作为实际节点名。这样既保证了系统接口清晰，也方便后续在 Mininet 中部署和调试。

---

## 4. 访问控制命令设计

访问控制场景对应的用户输入为：

```text
禁止学生网段访问管理服务器，但允许教师网段访问。
```

Intent Agent 将其解析为：

```json
{
  "intent_type": "access_control",
  "source": "student_host",
  "destination": "admin_server",
  "action": "deny",
  "constraint": null
}
```

Planner Agent 生成 ACL 策略：

```json
{
  "policy_type": "acl",
  "target": "student_to_admin",
  "method": "iptables",
  "expected_result": "student_host cannot reach admin_server; teacher_host can reach admin_server"
}
```

对应的底层命令设计为：

```bash
iptables -A FORWARD -s 10.0.0.1 -d 10.0.0.10 -j DROP
```

该命令的含义是：

```text
阻断源地址为 10.0.0.1 的 student_host 到目标地址 10.0.0.10 的 admin_server 的转发流量。
```

该策略预期达到的效果是：

```text
student_host 无法访问 admin_server
teacher_host 仍然可以访问 admin_server
```

---

## 5. 低延迟与自愈命令设计

低延迟保障场景对应的用户输入为：

```text
保证客户端到服务器的延迟低于50ms。
```

Intent Agent 将其解析为：

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

### 5.1 初始路径策略

Planner Agent 首先生成初始路径策略：

```json
{
  "policy_type": "latency_control",
  "target": "client_to_server",
  "method": "ovs",
  "expected_result": "client_host reaches server with latency < 50ms"
}
```

对应的底层命令设计为：

```bash
ovs-ofctl add-flow s3 priority=10,ip,nw_src=10.0.1.1,nw_dst=10.0.1.10,actions=output:primary
```

该命令表示系统尝试通过主路径转发 `client_host` 到 `server` 的流量。

### 5.2 延迟异常检测

在当前演示场景中，Verifier Agent 模拟检测到初始路径延迟过高：

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

该结果表示：

```text
当前路径不满足用户要求，需要触发重规划。
```

### 5.3 备用路径重规划策略

Planner Agent 根据反馈生成备用路径策略：

```json
{
  "policy_type": "reroute",
  "target": "client_to_server",
  "method": "ovs",
  "expected_result": "client_host reaches server with latency < 50ms",
  "reason": "current path latency is too high, please switch to backup path"
}
```

对应的底层命令设计为：

```bash
ovs-ofctl add-flow s3 priority=20,ip,nw_src=10.0.1.1,nw_dst=10.0.1.10,actions=output:backup
```

该命令表示系统将流量切换到备用路径，以绕开高延迟链路。

重规划后的验证结果为：

```json
{
  "verify_status": "success",
  "test_tool": "ping",
  "expected": "latency < 50ms",
  "actual": "latency = 35ms",
  "need_replan": false,
  "feedback": null
}
```

---

## 6. 遥测验证设计

网络验证主要由 Verifier Agent 完成，验证内容包括：

| 验证类型  | 工具设计                        | 验证目标              |
| ----- | --------------------------- | ----------------- |
| 可达性验证 | `ping`                      | 判断主机之间是否可达        |
| 延迟验证  | `ping` / `iperf`            | 判断端到端延迟是否满足阈值     |
| 路径验证  | `traceroute` / OVS 状态查询     | 判断流量是否切换到预期路径     |
| 故障验证  | link down / delay injection | 判断系统是否能检测异常并触发重规划 |

在当前 Windows 演示环境中，系统采用 mock execution mode，因此 Verifier Agent 使用稳定的模拟验证结果来展示完整闭环。该模式可以保证演示稳定，同时保留真实网络部署时需要的命令接口和验证逻辑。

---

## 7. 当前测试状态

当前版本已在 Windows 环境下完成完整流程测试。

测试命令：

```bash
python main.py --scenario access
python main.py --scenario latency
pytest
```

测试结果：

| 测试项         | 结果 |
| ----------- | -- |
| 访问控制场景      | 通过 |
| 低延迟保障场景     | 通过 |
| 失败后重规划      | 通过 |
| pytest 单元测试 | 通过 |

其中：

```text
访问控制场景 final_status = success
低延迟场景 final_status = success
pytest = 2 passed
```

---

## 8. 当前环境说明

当前版本在 Windows 环境中使用 mock execution mode 完成演示。

在该模式下：

```text
1. 系统会生成真实风格的网络命令。
2. Executor Agent 不会直接在 Windows 系统中执行 iptables 或 ovs-ofctl。
3. Verifier Agent 使用稳定模拟结果验证闭环流程。
4. 系统可以完整展示 Intent → Planner → Executor → Verifier → Replan 的多 Agent 工作流。
```

因此，当前版本已完成命令生成和闭环验证，真实 Mininet 测试作为后续部署方向。

这种设计可以避免在选拔赛演示阶段受到本地系统环境、权限、Mininet 依赖等因素影响，同时保留了向真实网络环境迁移的接口基础。

---

## 9. 后续 Linux / Mininet 迁移方向

后续如果部署到 Linux / Mininet 环境，可以进一步完成真实网络执行测试。

建议迁移步骤如下：

```text
1. 在 Linux 环境安装 Mininet、Open vSwitch 和 iptables。
2. 使用 network/mininet_topo.py 启动固定拓扑。
3. 验证 student_host、teacher_host 和 admin_server 初始连通性。
4. 执行 ACL 阻断命令，验证 student_host 无法访问 admin_server。
5. 验证 teacher_host 仍然可以访问 admin_server。
6. 使用 tc netem 注入链路延迟。
7. 使用 ping 或 iperf 测试 client_host 到 server 的延迟。
8. 当延迟超过阈值时，执行备用路径策略。
9. 再次验证延迟是否满足要求。
```

真实网络环境下可重点验证以下命令：

```bash
iptables -A FORWARD -s 10.0.0.1 -d 10.0.0.10 -j DROP

ovs-ofctl add-flow s3 priority=10,ip,nw_src=10.0.1.1,nw_dst=10.0.1.10,actions=output:primary

ovs-ofctl add-flow s3 priority=20,ip,nw_src=10.0.1.1,nw_dst=10.0.1.10,actions=output:backup

tc qdisc add dev <interface> root netem delay 120ms
```

---

## 10. 小结

当前网络模块已经完成选拔赛阶段所需的核心功能设计：

```text
1. 固定网络拓扑设计。
2. 访问控制命令生成。
3. 低延迟保障策略生成。
4. 失败反馈后的备用路径重规划。
5. Mock execution mode 下的稳定闭环验证。
6. 后续迁移到 Linux / Mininet 真实执行环境的接口基础。
```

当前版本适合作为选拔赛阶段的稳定演示版本。真实 Mininet 环境测试可作为后续增强方向。
