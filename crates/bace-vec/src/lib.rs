//! Batched parallel B-ACE environments.

use bace_core::{Action, AgentId, EndCondition, ScenarioConfig, SimSnapshot, Simulation, StepResult};
use bace_record::{EpisodeRecord, Recorder, StepRecord};
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VecEnvConfig {
    pub num_envs: usize,
    pub scenario: ScenarioConfig,
    pub record: bool,
    pub runs_dir: PathBuf,
}

impl Default for VecEnvConfig {
    fn default() -> Self {
        Self {
            num_envs: 1,
            scenario: ScenarioConfig::default(),
            record: false,
            runs_dir: PathBuf::from("runs"),
        }
    }
}

pub struct ParallelEnvs {
    pub envs: Vec<Simulation>,
    recorders: Vec<Option<Recorder>>,
    cfg: VecEnvConfig,
}

impl ParallelEnvs {
    pub fn new(cfg: VecEnvConfig) -> Self {
        let envs: Vec<_> = (0..cfg.num_envs)
            .map(|i| {
                let mut sc = cfg.scenario.clone();
                sc.env.seed = cfg.scenario.env.seed.wrapping_add(i as u64);
                Simulation::new(sc)
            })
            .collect();
        let recorders = envs
            .iter()
            .map(|e| {
                if cfg.record {
                    Recorder::new(&cfg.runs_dir, e.config.clone()).ok()
                } else {
                    None
                }
            })
            .collect();
        Self {
            envs,
            recorders,
            cfg,
        }
    }

    pub fn num_envs(&self) -> usize {
        self.envs.len()
    }

    pub fn reset_all(&mut self, seed: Option<u64>) -> Vec<StepResult> {
        self.envs
            .iter_mut()
            .enumerate()
            .map(|(i, env)| {
                let s = seed.map(|base| base.wrapping_add(i as u64));
                env.reset(s)
            })
            .collect()
    }

    pub fn step_all(&mut self, actions: &[HashMap<AgentId, Action>]) -> Vec<StepResult> {
        assert_eq!(actions.len(), self.envs.len());
        // Sequential recording bookkeeping; parallelize physics via rayon on owned chunks if needed.
        // For correctness with recorders, step sequentially per env but can parallelize without record.
        if self.cfg.record {
            self.envs
                .iter_mut()
                .zip(actions.iter())
                .zip(self.recorders.iter_mut())
                .map(|((env, acts), rec)| {
                    let result = env.step(acts);
                    if let Some(r) = rec {
                        r.push(StepRecord {
                            action_step: result.action_step,
                            actions: acts.clone(),
                            rewards: result
                                .agents
                                .iter()
                                .map(|(k, v)| (k.clone(), v.reward))
                                .collect(),
                            reward_breakdowns: result
                                .agents
                                .iter()
                                .map(|(k, v)| (k.clone(), v.reward_breakdown.clone()))
                                .collect(),
                            obs: result
                                .agents
                                .iter()
                                .map(|(k, v)| (k.clone(), v.obs.clone()))
                                .collect(),
                            snapshot: env.snapshot(),
                        });
                    }
                    result
                })
                .collect()
        } else {
            self.envs
                .par_iter_mut()
                .zip(actions.par_iter())
                .map(|(env, acts)| env.step(acts))
                .collect()
        }
    }

    pub fn snapshots(&self) -> Vec<SimSnapshot> {
        self.envs.iter().map(|e| e.snapshot()).collect()
    }

    pub fn finish_recordings(&mut self) -> Vec<Option<EpisodeRecord>> {
        let ends: Vec<EndCondition> = self.envs.iter().map(|e| e.end).collect();
        self.recorders
            .drain(..)
            .zip(ends)
            .map(|(rec, end)| rec.and_then(|r| r.finish(end).ok()))
            .collect()
    }
}

/// Run a grid of scenario configs (experiment mode).
pub fn run_experiment(
    cases: Vec<ScenarioConfig>,
    max_parallel: usize,
) -> Vec<(ScenarioConfig, EndCondition, u32)> {
    let chunk = max_parallel.max(1);
    cases
        .into_iter()
        .collect::<Vec<_>>()
        .par_chunks(chunk)
        .flat_map(|chunk| {
            chunk
                .iter()
                .map(|cfg| {
                    let mut sim = Simulation::new(cfg.clone());
                    sim.reset(Some(cfg.env.seed));
                    let empty = HashMap::new();
                    while sim.end == EndCondition::Ongoing {
                        sim.step(&empty);
                    }
                    (cfg.clone(), sim.end, sim.action_step)
                })
                .collect::<Vec<_>>()
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use bace_core::Behavior;

    #[test]
    fn parallel_duck_episode() {
        let mut scenario = ScenarioConfig::default();
        scenario.env.max_cycles = 20;
        scenario.blue.behavior = Behavior::Duck;
        scenario.red.behavior = Behavior::Duck;
        let mut pe = ParallelEnvs::new(VecEnvConfig {
            num_envs: 4,
            scenario,
            record: false,
            runs_dir: PathBuf::from("/tmp/bace_runs"),
        });
        pe.reset_all(Some(1));
        let actions: Vec<_> = (0..4).map(|_| HashMap::new()).collect();
        for _ in 0..5 {
            let results = pe.step_all(&actions);
            assert_eq!(results.len(), 4);
        }
    }
}
