//! Structured observations and actions (redesigned API).

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OwnObs {
    pub x: f64,
    pub z: f64,
    pub altitude: f64,
    pub dist_target: f64,
    pub aspect_to_target: f64,
    pub heading: f64,
    pub speed: f64,
    pub missiles: f64,
    pub supporting_missile: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AllyObs {
    pub id: u32,
    pub alt_diff: f64,
    pub aspect: f64,
    pub angle_off: f64,
    pub dist: f64,
    pub dist_target: f64,
    pub detected: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EnemyObs {
    pub id: u32,
    pub alt_diff: f64,
    pub aspect: f64,
    pub angle_off: f64,
    pub dist: f64,
    pub dist_target: f64,
    pub own_r_max: f64,
    pub own_r_nez: f64,
    pub enemy_r_max: f64,
    pub enemy_r_nez: f64,
    pub threat_factor: f64,
    pub offensive_factor: f64,
    pub is_missile_support: f64,
    pub detected: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StructuredObs {
    pub own: OwnObs,
    pub allies: Vec<AllyObs>,
    pub enemies: Vec<EnemyObs>,
}

impl StructuredObs {
    /// Flatten: own(9) + enemies(13 each) + allies(6 each).
    pub fn to_flat(&self) -> Vec<f64> {
        let mut out = Vec::with_capacity(Self::flat_size(self.allies.len(), self.enemies.len()));
        out.extend_from_slice(&[
            self.own.x,
            self.own.z,
            self.own.altitude,
            self.own.dist_target,
            self.own.aspect_to_target,
            self.own.heading,
            self.own.speed,
            self.own.missiles,
            self.own.supporting_missile,
        ]);
        for e in &self.enemies {
            out.extend_from_slice(&[
                e.alt_diff,
                e.aspect,
                e.angle_off,
                e.dist,
                e.dist_target,
                e.own_r_max,
                e.own_r_nez,
                e.enemy_r_max,
                e.enemy_r_nez,
                e.threat_factor,
                e.offensive_factor,
                e.is_missile_support,
                e.detected,
            ]);
        }
        for a in &self.allies {
            out.extend_from_slice(&[
                a.alt_diff,
                a.aspect,
                a.angle_off,
                a.dist,
                a.dist_target,
                a.detected,
            ]);
        }
        out
    }

    pub fn flat_size(n_allies: usize, n_enemies: usize) -> usize {
        9 + n_enemies * 13 + n_allies * 6
    }
}

/// Continuous low-level control in [-1, 1].
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct Action {
    pub d_heading: f64,
    pub d_altitude: f64,
    pub g_force: f64,
    pub fire: f64,
}

impl Default for Action {
    fn default() -> Self {
        Self {
            d_heading: 0.0,
            d_altitude: 0.0,
            g_force: -1.0,
            fire: -1.0,
        }
    }
}

impl Action {
    pub fn from_slice(a: &[f64]) -> Self {
        Self {
            d_heading: *a.first().unwrap_or(&0.0),
            d_altitude: *a.get(1).unwrap_or(&0.0),
            g_force: *a.get(2).unwrap_or(&-1.0),
            fire: *a.get(3).unwrap_or(&-1.0),
        }
    }

    pub fn to_vec(self) -> Vec<f64> {
        vec![self.d_heading, self.d_altitude, self.g_force, self.fire]
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct DiscreteAction {
    pub fire: u8,
    pub level: u8,
    pub turn: u8,
}

impl DiscreteAction {
    pub fn to_continuous(self) -> Action {
        let turn_deg = match self.turn {
            0 => -90.0,
            1 => -45.0,
            2 => 0.0,
            3 => 45.0,
            _ => 90.0,
        };
        let level = match self.level {
            0 => -1.0,
            1 => -0.5,
            2 => 0.0,
            3 => 0.5,
            _ => 1.0,
        };
        let g = match self.turn {
            0 | 4 => 1.0,
            1 | 3 => 0.0,
            _ => -1.0,
        };
        Action {
            d_heading: turn_deg / 180.0,
            d_altitude: level,
            g_force: g,
            fire: if self.fire > 0 { 1.0 } else { -1.0 },
        }
    }
}
