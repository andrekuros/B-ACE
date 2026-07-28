"""Simple GA over FSM d_shot / l_crank / l_break parameters."""

from __future__ import annotations

import argparse
import json
import random

import numpy as np

from bace import BaceEnv


def evaluate(params: dict, episodes: int, max_cycles: int, seed: int) -> float:
    wins = 0
    for i in range(episodes):
        env = BaceEnv(
            {
                "env": {"max_cycles": max_cycles, "seed": seed + i},
                "blue": {
                    "num_agents": 1,
                    "behavior": "baseline1",
                    "beh_config": {
                        "d_shot": [params["d_shot"]],
                        "l_crank": [params["l_crank"]],
                        "l_break": [params["l_break"]],
                    },
                },
                "red": {"num_agents": 1, "behavior": "duck"},
            }
        )
        env.reset(seed=seed + i)
        steps = 0
        while env.agents and steps < max_cycles + 5:
            actions = {a: np.zeros(4, dtype=np.float32) for a in env.agents}
            env.step(actions)
            steps += 1
        if env.state().get("end") == "red_killed":
            wins += 1
        env.close()
    return wins / max(episodes, 1)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--generations", type=int, default=5)
    p.add_argument("--pop", type=int, default=8)
    p.add_argument("--episodes", type=int, default=3)
    p.add_argument("--max-cycles", type=int, default=80)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    rng = random.Random(args.seed)
    pop = [
        {
            "d_shot": rng.uniform(0.5, 1.2),
            "l_crank": rng.uniform(0.4, 1.1),
            "l_break": rng.uniform(0.7, 1.3),
        }
        for _ in range(args.pop)
    ]

    best = None
    best_fit = -1.0
    history = []
    for g in range(args.generations):
        scored = []
        for ind in pop:
            fit = evaluate(ind, args.episodes, args.max_cycles, args.seed + g * 100)
            scored.append((fit, ind))
            if fit > best_fit:
                best_fit, best = fit, ind
        scored.sort(key=lambda x: x[0], reverse=True)
        history.append({"generation": g, "best_fit": scored[0][0], "best": scored[0][1]})
        elites = [ind for _, ind in scored[: max(2, args.pop // 4)]]
        new_pop = list(elites)
        while len(new_pop) < args.pop:
            parent = rng.choice(elites)
            child = {
                "d_shot": float(np.clip(parent["d_shot"] + rng.uniform(-0.1, 0.1), 0.3, 1.5)),
                "l_crank": float(np.clip(parent["l_crank"] + rng.uniform(-0.1, 0.1), 0.2, 1.5)),
                "l_break": float(np.clip(parent["l_break"] + rng.uniform(-0.1, 0.1), 0.5, 1.6)),
            }
            new_pop.append(child)
        pop = new_pop
        print(f"gen={g} best_fit={scored[0][0]:.3f} params={scored[0][1]}")

    out = {"best": best, "best_fit": best_fit, "history": history}
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
