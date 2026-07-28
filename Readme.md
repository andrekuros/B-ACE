# B-ACE 2.0

Beyond Visual Range Air Combat Environment — rebuilt as a **Rust-native** simulator with PettingZoo Python bindings and a local web dashboard.

## Why 2.0

B-ACE 1.0 ran kinematics inside Godot and talked to Python over TCP/JSON (one heavy process per env, fragile PettingZoo contract, no replay).  
**B-ACE 2.0** keeps the BVR research intent but redesigns the stack:

- High-performance **Rust** sim core (`bace-core`) with in-process parallel envs (`bace-vec`)
- Clean **PettingZoo ParallelEnv** API via PyO3
- **Web dashboard** for live parallel runs and episode replay
- Experiment mode + GA examples without a game engine binary

The Godot-based 1.0 tree lives under [`legacy/`](legacy/).

## Quick start

```bash
# Rust tests
cargo test -p bace-core -p bace-record -p bace-vec

# Python env
python3 -m venv .venv && source .venv/bin/activate
pip install maturin pytest pettingzoo gymnasium numpy
maturin develop -m crates/bace-py/Cargo.toml
pytest -q tests/python
python -m bace.examples.random_policy
```

### Dashboard

```bash
cargo run -p bace-server -- --port 8787 --static-dir web/dist --runs-dir runs
# open http://127.0.0.1:8787
```

## Python API

```python
from bace import BaceEnv

env = BaceEnv({
    "env": {"max_cycles": 500, "seed": 1},
    "blue": {"num_agents": 1, "behavior": "external"},
    "red": {"num_agents": 1, "behavior": "baseline1"},
})
obs, infos = env.reset(seed=1)
actions = {a: env.action_space(a).sample() for a in env.agents}
obs, rewards, terms, truncs, infos = env.step(actions)
```

Observations are structured in Rust and exported as a flat `float32` vector: own(9) + enemies(13 each) + allies(6 each).  
Continuous actions are `[d_heading, d_altitude, g_force, fire]` in `[-1, 1]`.

Behaviors: `external` (RL), `baseline1` (FSM), `duck`.

## Layout

| Path | Role |
|------|------|
| `crates/bace-core` | Physics, WEZ, missiles, radar, FSM, rewards |
| `crates/bace-vec` | Batched parallel envs + experiment runner |
| `crates/bace-record` | Episode JSON recordings under `runs/` |
| `crates/bace-py` | PyO3 native module |
| `crates/bace-server` | Axum HTTP/WS dashboard API |
| `python/bace` | PettingZoo wrapper |
| `web/dist` | Live + replay UI |
| `examples/` | Tianshou toy trainer, BenchMARL hook, experiment, GA |
| `legacy/` | B-ACE 1.0 Godot + old Python wrappers |

## Examples

```bash
python examples/tianshou/train_ddpg_toy.py --steps 200
python examples/benchmarl/run_pettingzoo_smoke.py
python examples/experiment/run_experiment.py --cases 8
python examples/ga/optimize_fsm.py --generations 3 --pop 6
```

## License

MIT — see [LICENSE](LICENSE).
