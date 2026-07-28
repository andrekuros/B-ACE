"""Experiment-mode batch runner via dashboard API or local Rust-equivalent loop."""

from __future__ import annotations

import argparse
import json
import urllib.request

from bace import BaceEnv


def run_local(cases: int, max_cycles: int) -> dict:
    results = []
    for i in range(cases):
        env = BaceEnv(
            {
                "env": {"max_cycles": max_cycles, "seed": i + 1},
                "blue": {
                    "num_agents": 1,
                    "behavior": "baseline1",
                    "beh_config": {
                        "d_shot": [0.7 + i * 0.01],
                        "l_crank": [0.6],
                        "l_break": [0.95],
                    },
                },
                "red": {"num_agents": 1, "behavior": "duck"},
            }
        )
        env.reset(seed=i + 1)
        steps = 0
        while env.agents and steps < max_cycles + 5:
            actions = {a: env.action_space(a).sample() * 0 for a in env.agents}
            # baseline1 ignores external actions when behavior is baseline1 —
            # but blue is baseline1 so empty/zero actions are fine.
            _, _, terms, truncs, _ = env.step(actions)
            steps += 1
            if all(terms.get(a, False) or truncs.get(a, False) for a in terms):
                break
        end = env.state().get("end")
        results.append({"seed": i + 1, "end": end, "steps": steps})
        env.close()
    wins = sum(1 for r in results if r["end"] == "red_killed")
    return {"cases": cases, "red_killed": wins, "results": results}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--cases", type=int, default=8)
    p.add_argument("--max-cycles", type=int, default=100)
    p.add_argument("--api", type=str, default="")
    args = p.parse_args()
    if args.api:
        req = urllib.request.Request(
            args.api.rstrip("/") + "/api/experiment",
            data=json.dumps({"cases": args.cases, "max_cycles": args.max_cycles}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            print(resp.read().decode())
    else:
        print(json.dumps(run_local(args.cases, args.max_cycles), indent=2))


if __name__ == "__main__":
    main()
