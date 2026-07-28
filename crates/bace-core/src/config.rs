//! Typed scenario configuration for B-ACE 2.0.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Behavior {
    External,
    Baseline1,
    Duck,
}

impl Default for Behavior {
    fn default() -> Self {
        Self::Baseline1
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Mission {
    Dca,
    Striker,
}

impl Default for Mission {
    fn default() -> Self {
        Self::Dca
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ActionType {
    Continuous,
    Discrete,
}

impl Default for ActionType {
    fn default() -> Self {
        Self::Continuous
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(default)]
pub struct Vec3Config {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

impl Default for Vec3Config {
    fn default() -> Self {
        Self {
            x: 0.0,
            y: 25000.0, // ft (converted at spawn)
            z: 30.0,    // NM
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(default)]
pub struct BehConfig {
    /// Shoot when range_ratio <= d_shot (range / RMax).
    pub d_shot: Vec<f64>,
    /// Crank when offensive_factor <= l_crank.
    pub l_crank: Vec<f64>,
    /// Break when threat_factor >= l_break.
    pub l_break: Vec<f64>,
}

impl Default for BehConfig {
    fn default() -> Self {
        Self {
            d_shot: vec![1.04, 0.50, 1.09],
            l_crank: vec![1.06, 0.98, 0.98],
            l_break: vec![1.05, 1.17, 0.45],
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(default)]
pub struct TeamConfig {
    pub num_agents: usize,
    pub share_tracks: bool,
    pub behavior: Behavior,
    pub mission: Mission,
    pub beh_config: BehConfig,
    pub init_position: Vec3Config,
    pub offset_pos: Vec3Config,
    pub init_hdg: f64,
    pub target_position: Vec3Config,
    pub rnd_offset_range: Vec3Config,
}

impl Default for TeamConfig {
    fn default() -> Self {
        Self {
            num_agents: 1,
            share_tracks: true,
            behavior: Behavior::Baseline1,
            mission: Mission::Dca,
            beh_config: BehConfig::default(),
            init_position: Vec3Config::default(),
            offset_pos: Vec3Config {
                x: 0.0,
                y: 0.0,
                z: 0.0,
            },
            init_hdg: 0.0,
            target_position: Vec3Config {
                x: 0.0,
                y: 25000.0,
                z: -30.0,
            },
            rnd_offset_range: Vec3Config {
                x: 0.0,
                y: 0.0,
                z: 0.0,
            },
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(default)]
pub struct RewardsConfig {
    pub mission_factor: f64,
    pub missile_fire_factor: f64,
    pub missile_no_fire_factor: f64,
    pub missile_miss_factor: f64,
    pub detect_loss_factor: f64,
    pub keep_track_factor: f64,
    pub hit_enemy_factor: f64,
    pub hit_own_factor: f64,
    pub mission_accomplished_factor: f64,
}

impl Default for RewardsConfig {
    fn default() -> Self {
        Self {
            mission_factor: 0.001,
            missile_fire_factor: -0.1,
            missile_no_fire_factor: -0.001,
            missile_miss_factor: -0.5,
            detect_loss_factor: -0.1,
            keep_track_factor: 0.001,
            hit_enemy_factor: 3.0,
            hit_own_factor: -5.0,
            mission_accomplished_factor: 10.0,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(default)]
pub struct EnvConfig {
    pub phy_fps: u32,
    pub speed_up: u32,
    pub max_cycles: u32,
    pub action_repeat: u32,
    pub action_type: ActionType,
    pub stop_mission: bool,
    pub seed: u64,
    pub rewards: RewardsConfig,
}

impl Default for EnvConfig {
    fn default() -> Self {
        Self {
            phy_fps: 20,
            speed_up: 1,
            max_cycles: 3600,
            action_repeat: 20,
            action_type: ActionType::Continuous,
            stop_mission: true,
            seed: 1,
            rewards: RewardsConfig::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(default)]
pub struct ScenarioConfig {
    pub env: EnvConfig,
    pub blue: TeamConfig,
    pub red: TeamConfig,
}

impl Default for ScenarioConfig {
    fn default() -> Self {
        let mut red = TeamConfig::default();
        red.init_position.z = -30.0;
        red.init_hdg = 180.0;
        red.target_position.z = 30.0;
        red.behavior = Behavior::Baseline1;
        Self {
            env: EnvConfig::default(),
            blue: TeamConfig {
                behavior: Behavior::External,
                ..TeamConfig::default()
            },
            red,
        }
    }
}

impl ScenarioConfig {
    pub fn from_json(s: &str) -> Result<Self, serde_json::Error> {
        serde_json::from_str(s)
    }

    pub fn to_json_pretty(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string_pretty(self)
    }

    /// Deep-merge overrides from a partial JSON object.
    pub fn merge_json(&mut self, partial: &str) -> Result<(), serde_json::Error> {
        let patch: serde_json::Value = serde_json::from_str(partial)?;
        let mut base = serde_json::to_value(&*self)?;
        merge_values(&mut base, &patch);
        *self = serde_json::from_value(base)?;
        Ok(())
    }
}

fn merge_values(base: &mut serde_json::Value, patch: &serde_json::Value) {
    match (base, patch) {
        (serde_json::Value::Object(b), serde_json::Value::Object(p)) => {
            for (k, v) in p {
                let entry = b.entry(k.clone()).or_insert(serde_json::Value::Null);
                merge_values(entry, v);
            }
        }
        (b, p) => *b = p.clone(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_roundtrip() {
        let c = ScenarioConfig::default();
        let s = c.to_json_pretty().unwrap();
        let c2 = ScenarioConfig::from_json(&s).unwrap();
        assert_eq!(c2.blue.num_agents, 1);
        assert_eq!(c2.env.phy_fps, 20);
    }

    #[test]
    fn deep_merge_preserves_rewards() {
        let mut c = ScenarioConfig::default();
        c.merge_json(r#"{"env":{"max_cycles":100}}"#).unwrap();
        assert_eq!(c.env.max_cycles, 100);
        assert!((c.env.rewards.hit_enemy_factor - 3.0).abs() < 1e-9);
    }
}
