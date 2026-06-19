# 测试报告

## 1. 测试目的

本文档用于记录 NetIntent-Agent 项目当前最终整合版本的功能测试结果。

本次测试的目的是验证系统是否能够完成以下核心闭环流程：

```text
自然语言输入
→ Intent Agent 意图解析
→ Planner Agent 策略规划
→ Executor Agent 配置执行
→ Verifier Agent 结果验证
→ 验证失败时触发重规划
→ 最终验证成功
```

当前版本重点测试两个核心演示场景：

1. 访问控制策略生成与验证。
2. 低延迟保障与反馈驱动的重规划自愈。

---

## 2. 测试环境

| 项目        | 内容                  |
| --------- | ------------------- |
| 操作系统      | Windows             |
| Python 版本 | Python 3.11.9       |
| 测试模式      | Mock execution mode |
| 项目入口      | `main.py`           |
| 测试框架      | `pytest`            |
| GUI 框架    | Streamlit           |

说明：当前测试在 Windows 环境下使用 mock execution mode。该模式下，系统会生成真实的网络配置命令，例如 `iptables` 和 `ovs-ofctl`，但不会直接在操作系统中执行这些命令。真实命令执行可在 Linux / Mininet 环境中进一步测试。

---

## 3. 测试命令

本次最终测试使用以下命令：

```bash
python main.py --scenario access
python main.py --scenario latency
pytest
```

---

## 4. 测试场景一：访问控制

### 4.1 用户输入

```text
禁止学生网段访问管理服务器，但允许教师网段访问。
```

### 4.2 预期流程

系统应完成以下步骤：

```text
自然语言输入
→ 解析访问控制意图
→ 生成 ACL 策略
→ 生成 iptables 命令
→ 验证 student_host 无法访问 admin_server
→ 验证 teacher_host 仍然可以访问 admin_server
```

### 4.3 Intent Agent 输出

```json
{
  "intent_type": "access_control",
  "source": "student_host",
  "destination": "admin_server",
  "action": "deny",
  "constraint": null
}
```

### 4.4 Planner Agent 输出

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

### 4.5 Executor Agent 执行结果

```json
{
  "execute_status": "success",
  "executed_command": "iptables -A FORWARD -s 10.0.0.1 -d 10.0.0.10 -j DROP",
  "message": "mock execution; set EXECUTE_REAL_COMMANDS=true to run"
}
```

### 4.6 Verifier Agent 验证结果

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

### 4.7 最终结果

```text
final_status = success
```

### 4.8 测试结论

访问控制场景测试通过。系统能够正确解析用户的访问控制需求，生成 ACL 策略，输出对应的 `iptables` 命令，并完成策略验证。

---

## 5. 测试场景二：低延迟保障与重规划

### 5.1 用户输入

```text
保证客户端到服务器的延迟低于50ms。
```

### 5.2 预期流程

系统应完成以下步骤：

```text
自然语言输入
→ 解析低延迟保障意图
→ 生成初始低延迟策略
→ 执行初始策略
→ 验证链路延迟
→ 检测到延迟不满足要求
→ 触发重规划
→ 生成备用路径策略
→ 执行备用路径策略
→ 再次验证
→ 最终验证成功
```

### 5.3 Intent Agent 输出

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

### 5.4 初始 Planner Agent 输出

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

### 5.5 初始验证结果

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

### 5.6 重规划结果

初始验证失败后，系统根据 Verifier Agent 的反馈触发重规划，Planner Agent 生成备用路径策略：

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

### 5.7 最终验证结果

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

### 5.8 最终结果

```text
final_status = success
```

### 5.9 测试结论

低延迟保障场景测试通过。系统能够识别延迟约束，在初始路径不满足要求时检测到异常，并通过反馈驱动 Planner Agent 重新规划备用路径。重规划后，系统再次验证并确认延迟满足要求。

该场景体现了系统的闭环验证能力和网络自愈能力。

---

## 6. 单元测试结果

本次单元测试使用以下命令：

```bash
pytest
```

测试结果如下：

```text
collected 2 items

tests/test_pipeline.py .. [100%]

2 passed
```

该结果说明当前系统主流程相关测试全部通过。

---

## 7. 最终测试汇总

| 测试项目        | 测试结果 |
| ----------- | ---- |
| 访问控制场景      | 通过   |
| 低延迟保障场景     | 通过   |
| 反馈驱动重规划     | 通过   |
| 最终验证        | 通过   |
| pytest 单元测试 | 通过   |

最终结论：

```text
当前整合版本已通过最终功能测试。
```

---

## 8. 真实网络部署说明

当前最终测试在 Windows 环境下以 mock execution mode 运行，适合验证多智能体流程、命令生成、日志记录、验证逻辑和重规划机制。

如果部署到真实网络仿真环境，可以在 Linux / Mininet 环境中启用真实命令执行。届时系统生成的 `iptables`、`ovs-ofctl`、`tc netem` 等命令可以作用于 Mininet 拓扑。

真实网络环境下建议重点验证：

```text
1. 启动 Mininet 网络拓扑。
2. 验证初始主机连通性。
3. 应用访问控制 ACL 策略。
4. 使用 ping 验证访问控制是否生效。
5. 模拟链路延迟或拥塞。
6. 触发重规划和备用路径选择。
7. 验证最终网络状态是否满足原始意图。
```

---

## 9. 匿名提交检查

正式提交前，需要检查所有材料是否满足匿名要求：

```text
1. 文档中不出现学校名称。
2. 文档中不出现团队成员姓名。
3. 文档中不出现指导教师姓名。
4. 截图或视频中不出现学校标识。
5. 截图或视频中不出现包含个人身份信息的本地路径。
6. 演示视频中不出现 GitHub 个人主页、邮箱、账号头像等身份信息。
7. 源代码 ZIP 中不包含缓存文件或临时文件。
```

最终源代码压缩包中不应包含：

```text
__pycache__/
.pytest_cache/
*.pyc
.git/
*.zip
netintent_agent_member1/
```

---

## 10. 结论

本次最终测试表明，NetIntent-Agent 当前版本已经能够完成从自然语言意图输入到策略生成、配置执行、结果验证和失败重规划的完整闭环。

系统已支持两个核心演示场景：

```text
1. 访问控制策略生成与验证。
2. 低延迟保障与反馈驱动的重规划自愈。
```

