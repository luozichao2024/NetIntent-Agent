from __future__ import annotations

import argparse
import json

from pipeline import run_pipeline

SCENARIOS = {
    "access": "禁止学生网段访问管理服务器，但允许教师网段访问。",
    "latency": "保证客户端到服务器的延迟低于50ms。",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="NetIntent-Agent command line demo")
    parser.add_argument("--input", type=str, default=None, help="自然语言网络需求")
    parser.add_argument("--scenario", choices=SCENARIOS.keys(), default=None, help="预设演示场景")
    args = parser.parse_args()

    user_input = args.input or SCENARIOS.get(args.scenario or "access")
    result = run_pipeline(user_input)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
