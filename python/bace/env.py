"""PettingZoo ParallelEnv for B-ACE 2.0."""

from __future__ import annotations

import json
from typing import Any, Optional

import numpy as np
from gymnasium import spaces
from pettingzoo import ParallelEnv

try:
    from bace._native import NativeEnv
except ImportError as exc:  # pragma: no cover
    NativeEnv = None  # type: ignore
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


def _default_config() -> dict[str, Any]:
    return {
        "env": {
            "phy_fps": 20,
            "max_cycles": 3600,
            "action_repeat": 20,
            "action_type": "continuous",
            "stop_mission": True,
            "seed": 1,
            "rewards": {},
        },
        "blue": {
            "num_agents": 1,
            "behavior": "external",
            "mission": "dca",
            "share_tracks": True,
        },
        "red": {
            "num_agents": 1,
            "behavior": "baseline1",
            "mission": "dca",
            "share_tracks": True,
            "init_position": {"x": 0.0, "y": 25000.0, "z": -30.0},
            "init_hdg": 180.0,
            "target_position": {"x": 0.0, "y": 25000.0, "z": 30.0},
        },
    }


class BaceEnv(ParallelEnv):
    """Multi-agent BVR environment backed by the Rust native core."""

    metadata = {"name": "bace_v2", "render_modes": []}

    def __init__(self, config: Optional[dict[str, Any]] = None, **kwargs: Any):
        if NativeEnv is None:
            raise ImportError(
                "bace native extension is not built. Run: pip install -e . "
                f"(maturin). Original error: {_IMPORT_ERROR}"
            )
        cfg = _default_config()
        if config:
            cfg = _deep_merge(cfg, config)
        if kwargs:
            cfg = _deep_merge(cfg, kwargs)
        self._config = cfg
        self._native = NativeEnv(json.dumps(cfg))
        self.possible_agents = list(self._native.agent_ids())
        self.agents = list(self.possible_agents)
        self._obs_size = int(self._native.obs_size())
        self._observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(self._obs_size,), dtype=np.float32
        )
        self._action_space = spaces.Box(
            low=-1.0, high=1.0, shape=(4,), dtype=np.float32
        )
        self._last: dict[str, Any] = {}

    def observation_space(self, agent: str) -> spaces.Space:
        return self._observation_space

    def action_space(self, agent: str) -> spaces.Space:
        return self._action_space

    def reset(
        self, seed: Optional[int] = None, options: Optional[dict] = None
    ) -> tuple[dict[str, np.ndarray], dict[str, dict]]:
        del options
        raw = self._native.reset(seed)
        self.agents = list(self.possible_agents)
        obs = {a: np.asarray(raw["obs"][a], dtype=np.float32) for a in self.agents}
        infos = {a: dict(raw["infos"].get(a, {})) for a in self.agents}
        self._last = raw
        return obs, infos

    def step(
        self, actions: dict[str, np.ndarray | list[float]]
    ) -> tuple[
        dict[str, np.ndarray],
        dict[str, float],
        dict[str, bool],
        dict[str, bool],
        dict[str, dict],
    ]:
        payload = {a: np.asarray(v, dtype=np.float64).reshape(-1).tolist() for a, v in actions.items()}
        raw = self._native.step(payload)
        obs = {a: np.asarray(raw["obs"][a], dtype=np.float32) for a in raw["obs"]}
        rewards = {a: float(raw["rewards"][a]) for a in raw["rewards"]}
        terminations = {a: bool(raw["terminations"][a]) for a in raw["terminations"]}
        truncations = {a: bool(raw["truncations"][a]) for a in raw["truncations"]}
        infos = {a: dict(raw["infos"].get(a, {})) for a in raw["infos"]}
        self.agents = [
            a
            for a in self.agents
            if not (terminations.get(a, False) or truncations.get(a, False))
        ]
        self._last = raw
        return obs, rewards, terminations, truncations, infos

    def state(self) -> dict[str, Any]:
        return json.loads(self._native.snapshot_json())

    def close(self) -> None:
        self.agents = []


def _deep_merge(base: dict, patch: dict) -> dict:
    out = dict(base)
    for k, v in patch.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out
