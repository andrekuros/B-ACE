//! Per-agent reward accumulator with named breakdown.

use crate::config::RewardsConfig;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct RewardBreakdown {
    pub mission: f64,
    pub missile_fire: f64,
    pub missile_no_fire: f64,
    pub missile_miss: f64,
    pub detect_loss: f64,
    pub keep_track: f64,
    pub hit_enemy: f64,
    pub hit_own: f64,
    pub terminal: f64,
}

impl RewardBreakdown {
    pub fn total(&self) -> f64 {
        self.mission
            + self.missile_fire
            + self.missile_no_fire
            + self.missile_miss
            + self.detect_loss
            + self.keep_track
            + self.hit_enemy
            + self.hit_own
            + self.terminal
    }
}

#[derive(Debug, Clone)]
pub struct Rewards {
    cfg: RewardsConfig,
    step: RewardBreakdown,
    cum: RewardBreakdown,
}

impl Rewards {
    pub fn new(cfg: RewardsConfig) -> Self {
        Self {
            cfg,
            step: RewardBreakdown::default(),
            cum: RewardBreakdown::default(),
        }
    }

    pub fn reset(&mut self) {
        self.step = RewardBreakdown::default();
        self.cum = RewardBreakdown::default();
    }

    fn add(field: &mut f64, cum: &mut f64, v: f64) {
        *field += v;
        *cum += v;
    }

    pub fn add_mission(&mut self, shaped: f64) {
        Self::add(
            &mut self.step.mission,
            &mut self.cum.mission,
            shaped * self.cfg.mission_factor,
        );
    }

    pub fn add_missile_fire(&mut self) {
        Self::add(
            &mut self.step.missile_fire,
            &mut self.cum.missile_fire,
            self.cfg.missile_fire_factor,
        );
    }

    pub fn add_missile_no_fire(&mut self) {
        Self::add(
            &mut self.step.missile_no_fire,
            &mut self.cum.missile_no_fire,
            self.cfg.missile_no_fire_factor,
        );
    }

    pub fn add_missile_miss(&mut self) {
        Self::add(
            &mut self.step.missile_miss,
            &mut self.cum.missile_miss,
            self.cfg.missile_miss_factor,
        );
    }

    pub fn add_detect_loss(&mut self, multiplier: f64) {
        Self::add(
            &mut self.step.detect_loss,
            &mut self.cum.detect_loss,
            self.cfg.detect_loss_factor * multiplier,
        );
    }

    pub fn add_keep_track(&mut self) {
        Self::add(
            &mut self.step.keep_track,
            &mut self.cum.keep_track,
            self.cfg.keep_track_factor,
        );
    }

    pub fn add_hit_enemy(&mut self) {
        Self::add(
            &mut self.step.hit_enemy,
            &mut self.cum.hit_enemy,
            self.cfg.hit_enemy_factor,
        );
    }

    pub fn add_hit_own(&mut self) {
        Self::add(
            &mut self.step.hit_own,
            &mut self.cum.hit_own,
            self.cfg.hit_own_factor,
        );
    }

    pub fn add_terminal(&mut self, kind: &str, _missiles_remaining: u32) {
        let v = match kind {
            "Enemies_Killed" | "Mission_Completed" => self.cfg.mission_accomplished_factor,
            "Team_Killed" | "Enemy_Achieved_Target" => -self.cfg.mission_accomplished_factor,
            "Max_Cycles" => 0.0,
            _ => 0.0,
        };
        Self::add(&mut self.step.terminal, &mut self.cum.terminal, v);
    }

    /// Take per-step reward and zero the step bucket.
    pub fn take_step(&mut self) -> (f64, RewardBreakdown) {
        let bd = self.step.clone();
        let total = bd.total();
        self.step = RewardBreakdown::default();
        (total, bd)
    }

    pub fn cumulative(&self) -> &RewardBreakdown {
        &self.cum
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::RewardsConfig;

    #[test]
    fn hit_and_take() {
        let mut r = Rewards::new(RewardsConfig::default());
        r.add_hit_enemy();
        let (t, bd) = r.take_step();
        assert!((t - 3.0).abs() < 1e-9);
        assert!((bd.hit_enemy - 3.0).abs() < 1e-9);
        let (t2, _) = r.take_step();
        assert!(t2.abs() < 1e-12);
    }
}
