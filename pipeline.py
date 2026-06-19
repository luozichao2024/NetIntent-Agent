from __future__ import annotations

from typing import Any

from agents.executor_agent import execute_policy
from agents.intent_agent import parse_intent
from agents.planner_agent import plan_policy
from agents.verifier_agent import verify_policy
from utils import append_run_log, load_topology, now_iso


def _step(name: str, input_data: Any, output_data: Any) -> dict:
    return {"step": name, "timestamp": now_iso(), "input": input_data, "output": output_data}


def run_pipeline(user_input: str) -> dict:
    topology = load_topology()
    logs = []

    intent = parse_intent(user_input)
    logs.append(_step("Intent Agent", user_input, intent))

    policy = plan_policy(intent, topology, feedback_json=None)
    logs.append(_step("Planner Agent", {"intent": intent, "feedback": None}, policy))

    execute_result = execute_policy(policy)
    logs.append(_step("Executor Agent", policy, execute_result))

    verify_result = verify_policy(intent, policy)
    logs.append(_step("Verifier Agent", {"intent": intent, "policy": policy}, verify_result))

    replan_result = None
    final_verify_result = verify_result
    final_status = "success" if verify_result.get("verify_status") == "success" else "failed"

    if verify_result.get("need_replan"):
        new_policy = plan_policy(intent, topology, feedback_json=verify_result)
        logs.append(_step("Planner Agent Replan", {"intent": intent, "feedback": verify_result}, new_policy))

        new_execute_result = execute_policy(new_policy)
        logs.append(_step("Executor Agent Replan", new_policy, new_execute_result))

        new_verify_result = verify_policy(intent, new_policy)
        logs.append(_step("Verifier Agent Recheck", {"intent": intent, "policy": new_policy}, new_verify_result))

        replan_result = {
            "policy": new_policy,
            "execute_result": new_execute_result,
            "verify_result": new_verify_result,
        }
        final_verify_result = new_verify_result
        final_status = "success" if new_verify_result.get("verify_status") == "success" else "failed"

    result = {
        "user_input": user_input,
        "intent": intent,
        "policy": policy,
        "execute_result": execute_result,
        "verify_result": verify_result,
        "replan_result": replan_result,
        "final_verify_result": final_verify_result,
        "final_status": final_status,
        "logs": logs,
    }
    append_run_log(result)
    return result
