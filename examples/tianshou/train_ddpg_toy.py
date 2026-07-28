"""Minimal Tianshou training loop on B-ACE 2.0 (optional torch/tianshou)."""

from __future__ import annotations

import argparse

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    try:
        import torch
        from torch import nn
    except ImportError:
        print("torch not installed; running random rollout fallback")
        _random_rollout(args.steps, args.seed)
        return

    from bace import BaceEnv

    env = BaceEnv(
        {
            "env": {"max_cycles": 200, "seed": args.seed},
            "blue": {"num_agents": 1, "behavior": "external"},
            "red": {"num_agents": 1, "behavior": "duck"},
        }
    )
    obs, _ = env.reset(seed=args.seed)
    obs_dim = obs["agent_0"].shape[0]
    act_dim = 4

    policy = nn.Sequential(
        nn.Linear(obs_dim, 64),
        nn.Tanh(),
        nn.Linear(64, act_dim),
        nn.Tanh(),
    )
    optim = torch.optim.Adam(policy.parameters(), lr=1e-3)

    returns = []
    ep_ret = 0.0
    for t in range(args.steps):
        o = torch.tensor(obs["agent_0"], dtype=torch.float32)
        with torch.no_grad():
            a = policy(o).numpy()
        a = a + 0.1 * np.random.randn(act_dim)
        a = np.clip(a, -1, 1).astype(np.float32)
        next_obs, rewards, terms, truncs, _ = env.step({"agent_0": a})
        r = float(rewards["agent_0"])
        ep_ret += r
        # simple policy gradient surrogate on reward signal
        loss = -policy(o)[0] * r  # toy objective
        optim.zero_grad()
        loss.backward()
        optim.step()
        obs = next_obs
        if terms["agent_0"] or truncs["agent_0"] or not env.agents:
            returns.append(ep_ret)
            ep_ret = 0.0
            obs, _ = env.reset(seed=args.seed + t + 1)
    env.close()
    print(
        f"tianshou-style toy trainer finished steps={args.steps} "
        f"episodes={len(returns)} mean_return={np.mean(returns) if returns else float('nan'):.3f}"
    )


def _random_rollout(steps: int, seed: int) -> None:
    from bace import BaceEnv

    env = BaceEnv(
        {
            "env": {"max_cycles": steps, "seed": seed},
            "blue": {"num_agents": 1, "behavior": "external"},
            "red": {"num_agents": 1, "behavior": "duck"},
        }
    )
    obs, _ = env.reset(seed=seed)
    total = 0.0
    for _ in range(steps):
        if not env.agents:
            break
        actions = {a: env.action_space(a).sample() for a in env.agents}
        obs, rewards, terms, truncs, _ = env.step(actions)
        total += float(sum(rewards.values()))
        if any(terms.values()) or any(truncs.values()):
            break
    print(f"random rollout return={total:.3f}")
    env.close()


if __name__ == "__main__":
    main()
