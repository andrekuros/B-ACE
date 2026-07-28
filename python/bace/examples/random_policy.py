"""Random-policy smoke example."""

from __future__ import annotations

import numpy as np

from bace import BaceEnv


def main() -> None:
    env = BaceEnv(
        {
            "env": {"max_cycles": 100, "seed": 42},
            "blue": {"num_agents": 1, "behavior": "external"},
            "red": {"num_agents": 1, "behavior": "duck"},
        }
    )
    obs, info = env.reset(seed=42)
    print("agents:", env.agents, "obs_dim:", next(iter(obs.values())).shape)
    total = {a: 0.0 for a in env.agents}
    for step in range(50):
        actions = {a: env.action_space(a).sample() for a in env.agents}
        obs, rewards, terms, truncs, infos = env.step(actions)
        for a, r in rewards.items():
            total[a] = total.get(a, 0.0) + r
        if not env.agents:
            print(f"episode ended at step {step}")
            break
    print("cumulative rewards:", total)
    print("final state end:", env.state().get("end"))
    env.close()


if __name__ == "__main__":
    main()
