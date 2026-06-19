# 成员1集成说明

## 主流程

`pipeline.run_pipeline(user_input)` 串联四个Agent：

1. `parse_intent(user_input)`
2. `plan_policy(intent, topology, feedback_json=None)`
3. `execute_policy(policy)`
4. `verify_policy(intent, policy)`
5. 若 `need_replan=true`，再次调用 Planner、Executor、Verifier。

## 其他成员接入方式

- 成员2只需要替换 `network/network_control.py` 和 `network/telemetry.py` 内部实现，保持函数签名不变。
- 成员3只需要替换 `agents/intent_agent.py` 和 `agents/planner_agent.py` 内部实现，保持JSON字段不变。
- 成员4只需要在GUI中调用 `run_pipeline(user_input)`，不要复制主流程逻辑。

## 日志

每次运行都会追加写入 `logs/run_logs.json`，包含输入、Agent输出、执行命令、验证结果、重规划结果和最终状态。
