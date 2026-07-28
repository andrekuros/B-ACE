"""BenchMARL / TorchRL-oriented PettingZoo registration smoke example."""

from __future__ import annotations

from bace import BaceEnv


def make_env(**kwargs):
    cfg = {
        "env": {"max_cycles": 100, "seed": 1},
        "blue": {"num_agents": 2, "behavior": "external"},
        "red": {"num_agents": 2, "behavior": "baseline1"},
    }
    cfg.update(kwargs)
    return BaceEnv(cfg)


def main() -> None:
    env = make_env()
    obs, info = env.reset(seed=1)
    print("BenchMARL-ready ParallelEnv agents:", list(obs))
    actions = {a: env.action_space(a).sample() for a in env.agents}
    obs, rewards, terms, truncs, infos = env.step(actions)
    print("step ok rewards=", rewards)
    env.close()
    print(
        "Hook this env into BenchMARL via custom task factory returning make_env()."
    )


if __name__ == "__main__":
    main()
