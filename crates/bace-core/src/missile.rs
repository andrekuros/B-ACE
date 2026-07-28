//! Missile guidance (kinematic, pitbull + uplink support).

use crate::geometry::{aspect_angle, clamp_hdg, distance2d, heading_to};
use crate::units::SConv;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Missile {
    pub id: u32,
    pub shooter_id: u32,
    pub target_id: u32,
    pub team: u8,
    pub pos: [f64; 3],
    pub hdg: f64,
    pub speed: f64,
    pub alive: bool,
    pub pitbull: bool,
    pub has_support: bool,
    pub time_alive: f64,
    pub max_time: f64,
    pub hit_radius: f64,
}

impl Missile {
    pub fn launch(
        id: u32,
        shooter_id: u32,
        target_id: u32,
        team: u8,
        pos: [f64; 3],
        hdg: f64,
    ) -> Self {
        Self {
            id,
            shooter_id,
            target_id,
            team,
            pos,
            hdg,
            speed: 900.0 * SConv::KNOT2GDM_S, // ~Mach-ish simplified
            alive: true,
            pitbull: false,
            has_support: true,
            time_alive: 0.0,
            max_time: 120.0,
            hit_radius: 0.5, // 50m
        }
    }

    pub fn lost_support(&mut self) {
        self.has_support = false;
    }

    pub fn recover_support(&mut self) {
        if !self.pitbull {
            self.has_support = true;
        }
    }

    /// Integrate one physics tick. Returns true if target was hit.
    pub fn tick(&mut self, dt: f64, target_pos: Option<[f64; 3]>, target_alive: bool) -> bool {
        if !self.alive {
            return false;
        }
        self.time_alive += dt;
        if self.time_alive > self.max_time {
            self.alive = false;
            return false;
        }

        if let Some(tp) = target_pos {
            let range = distance2d(self.pos, tp);
            // Pitbull at ~10 NM
            if range < 10.0 * SConv::NM2GDM {
                self.pitbull = true;
            }

            let can_guide = self.pitbull || self.has_support;
            if can_guide && target_alive {
                let desired = heading_to(self.pos, tp);
                let err = clamp_hdg(desired - self.hdg);
                let turn_rate = 120.0_f64.to_radians(); // rad/s aggressive
                let max_turn = turn_rate * dt;
                let turn = err.to_radians().clamp(-max_turn, max_turn);
                self.hdg = clamp_hdg(self.hdg + turn.to_degrees());

                if range < self.hit_radius {
                    self.alive = false;
                    return true;
                }
            } else if !target_alive {
                // coast until timeout
            }
        } else {
            // no track — coast
            if !self.pitbull {
                // without support and no pitbull, die sooner
                if !self.has_support && self.time_alive > 15.0 {
                    self.alive = false;
                    return false;
                }
            }
        }

        let rad = self.hdg.to_radians();
        // Forward is -Z in Godot convention
        self.pos[0] += rad.sin() * self.speed * dt;
        self.pos[2] += -rad.cos() * self.speed * dt;
        false
    }

    pub fn aspect_to_target(&self, target_pos: [f64; 3]) -> f64 {
        let brg = heading_to(self.pos, target_pos);
        aspect_angle(self.hdg, brg)
    }
}
