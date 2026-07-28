//! Kinematic fighter agent with radar tracks and FSM baselines.

use crate::config::{BehConfig, Behavior, Mission, RewardsConfig};
use crate::geometry::{
    angle_off, aspect_angle, clamp_hdg, desired_heading, distance2d, heading_to,
};
use crate::obs::{Action, AllyObs, EnemyObs, OwnObs, StructuredObs};
use crate::rewards::Rewards;
use crate::units::SConv;
use crate::wez::{self, WezRanges};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
pub enum FsmState {
    #[default]
    Search,
    Engage,
    MissileSupport,
    Evade,
}

#[derive(Debug, Clone)]
pub struct Track {
    pub id: u32,
    pub detected: bool,
    pub is_missile_support: bool,
    pub aspect: f64,
    pub angle_off: f64,
    pub dist: f64,
    pub alt_diff: f64,
    pub own_wez: WezRanges,
    pub enemy_wez: WezRanges,
    pub threat_factor: f64,
    pub offensive_factor: f64,
}

impl Track {
    pub fn blank(id: u32) -> Self {
        Self {
            id,
            detected: false,
            is_missile_support: false,
            aspect: 0.0,
            angle_off: 0.0,
            dist: -1.0,
            alt_diff: 0.0,
            own_wez: WezRanges {
                r_max: 0.01,
                r_nez: 0.01,
            },
            enemy_wez: WezRanges {
                r_max: 0.01,
                r_nez: 0.01,
            },
            threat_factor: 0.0,
            offensive_factor: 0.0,
        }
    }
}

/// Snapshot of another aircraft for sensing.
#[derive(Debug, Clone, Copy)]
pub struct AircraftView {
    pub id: u32,
    pub pos: [f64; 3],
    pub hdg: f64,
    pub alive: bool,
    pub dist2go: f64,
}

#[derive(Debug, Clone)]
pub struct Fighter {
    pub id: u32,
    pub team: u8,
    pub pos: [f64; 3],
    pub hdg: f64,
    pub pitch: f64,
    pub speed: f64,
    pub alive: bool,
    pub missiles: u32,
    pub behavior: Behavior,
    pub mission: Mission,
    pub beh: BehConfig,
    pub target_pos: [f64; 3],
    pub dist2go: f64,
    pub fsm: FsmState,
    pub hpt_id: Option<u32>,
    pub supporting_missile: bool,
    pub in_flight_missile_id: Option<u32>,
    pub share_tracks: bool,
    pub rewards: Rewards,
    pub done: bool,
    pub hdg_cmd: f64,
    pub level_cmd: f64,
    pub g_cmd: f64,
    pub fire_cmd: bool,
    pub radar_range: f64,
    pub radar_hfov: f64,
    pub radar_vfov_up: f64,
    pub radar_vfov_down: f64,
    pub max_speed: f64,
    pub max_g: f64,
    pub max_level: f64,
    pub min_level: f64,
    pub enemy_tracks: Vec<Track>,
    pub ally_ids: Vec<u32>,
}

impl Fighter {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        id: u32,
        team: u8,
        pos: [f64; 3],
        hdg: f64,
        target_pos: [f64; 3],
        behavior: Behavior,
        mission: Mission,
        beh: BehConfig,
        share_tracks: bool,
        rewards_cfg: RewardsConfig,
        enemy_ids: &[u32],
        ally_ids: Vec<u32>,
    ) -> Self {
        Self {
            id,
            team,
            pos,
            hdg: clamp_hdg(hdg),
            pitch: 0.0,
            speed: 650.0 * SConv::KNOT2GDM_S,
            alive: true,
            missiles: 6,
            behavior,
            mission,
            beh,
            target_pos,
            dist2go: distance2d(pos, target_pos),
            fsm: FsmState::Search,
            hpt_id: None,
            supporting_missile: false,
            in_flight_missile_id: None,
            share_tracks,
            rewards: Rewards::new(rewards_cfg),
            done: false,
            hdg_cmd: clamp_hdg(hdg),
            level_cmd: pos[1],
            g_cmd: 1.0,
            fire_cmd: false,
            radar_range: 50.0 * SConv::NM2GDM,
            radar_hfov: 60.0,
            radar_vfov_up: 40.0,
            radar_vfov_down: 20.0,
            max_speed: 650.0 * SConv::KNOT2GDM_S,
            max_g: 9.0,
            max_level: 50000.0 * SConv::FT2GDM,
            min_level: 1000.0 * SConv::FT2GDM,
            enemy_tracks: enemy_ids.iter().map(|&eid| Track::blank(eid)).collect(),
            ally_ids,
        }
    }

    fn altitude_speed_factor(alt: f64) -> f64 {
        0.2 * alt / 76.2 + 0.8
    }

    fn altitude_g_factor(alt: f64) -> f64 {
        (-0.5 * alt / 76.2 + 1.5).max(0.3)
    }

    pub fn apply_action(&mut self, action: Action) {
        self.hdg_cmd = desired_heading(self.hdg, action.d_heading.clamp(-1.0, 1.0));
        let level_ft = action.d_altitude.clamp(-1.0, 1.0) * 25000.0 + 25000.0;
        self.level_cmd = (level_ft * SConv::FT2GDM).clamp(self.min_level, self.max_level);
        self.g_cmd =
            (action.g_force.clamp(-1.0, 1.0) * (self.max_g - 1.0) + (self.max_g + 1.0)) / 2.0;
        self.fire_cmd = action.fire > 0.0;
    }

    pub fn is_detectable(&self, other_pos: [f64; 3]) -> bool {
        let dist = distance2d(self.pos, other_pos);
        if dist > self.radar_range || dist < 1e-6 {
            return false;
        }
        let brg = heading_to(self.pos, other_pos);
        if aspect_angle(self.hdg, brg).abs() > self.radar_hfov {
            return false;
        }
        let elev = ((other_pos[1] - self.pos[1]) / dist).atan().to_degrees();
        elev >= -self.radar_vfov_down && elev <= self.radar_vfov_up
    }

    pub fn update_tracks(&mut self, enemies: &[AircraftView], dl_detected: &[u32]) {
        let own_pos = self.pos;
        let own_hdg = self.hdg;
        let radar_range = self.radar_range;
        let radar_hfov = self.radar_hfov;
        let radar_vfov_up = self.radar_vfov_up;
        let radar_vfov_down = self.radar_vfov_down;
        let share_tracks = self.share_tracks;

        let detectable = |other_pos: [f64; 3]| -> bool {
            let dist = distance2d(own_pos, other_pos);
            if dist > radar_range || dist < 1e-6 {
                return false;
            }
            let brg = heading_to(own_pos, other_pos);
            if aspect_angle(own_hdg, brg).abs() > radar_hfov {
                return false;
            }
            let elev = ((other_pos[1] - own_pos[1]) / dist).atan().to_degrees();
            elev >= -radar_vfov_down && elev <= radar_vfov_up
        };

        for track in &mut self.enemy_tracks {
            let Some(enemy) = enemies.iter().find(|e| e.id == track.id) else {
                continue;
            };
            if !enemy.alive {
                if track.detected {
                    let mult = if track.is_missile_support { 5.0 } else { 1.0 };
                    self.rewards.add_detect_loss(mult);
                }
                track.detected = false;
                track.dist = -1.0;
                continue;
            }

            let was = track.detected;
            let local = detectable(enemy.pos);
            let via_dl = dl_detected.contains(&track.id);
            track.detected = local || (share_tracks && via_dl);

            if was && !track.detected {
                let mult = if track.is_missile_support { 5.0 } else { 1.0 };
                self.rewards.add_detect_loss(mult);
            }

            if track.detected {
                self.rewards.add_keep_track();
                let dist = distance2d(own_pos, enemy.pos);
                let brg = heading_to(own_pos, enemy.pos);
                track.aspect = aspect_angle(own_hdg, brg);
                track.angle_off = angle_off(own_hdg, enemy.hdg);
                track.dist = dist;
                track.alt_diff = (own_pos[1] - enemy.pos[1]) / 150.0;
                track.own_wez = wez::evaluate(own_pos[1], track.aspect, track.angle_off);
                let inv_asp = aspect_angle(enemy.hdg, heading_to(enemy.pos, own_pos));
                let inv_off = angle_off(enemy.hdg, own_hdg);
                track.enemy_wez = wez::evaluate(enemy.pos[1], inv_asp, inv_off);
                track.offensive_factor =
                    wez::offensive_factor(dist, track.own_wez.r_max, track.own_wez.r_nez);
                track.threat_factor =
                    wez::threat_factor(dist, track.enemy_wez.r_max, track.enemy_wez.r_nez);
            } else {
                track.dist = -1.0;
            }
        }

        let mut best_off = -1.0;
        let mut hpt = None;
        for t in &self.enemy_tracks {
            if t.detected && t.offensive_factor >= best_off {
                best_off = t.offensive_factor;
                hpt = Some(t.id);
            }
        }
        if hpt.is_none() {
            let mut best_thr = -1.0;
            for t in &self.enemy_tracks {
                if t.detected && t.threat_factor >= best_thr {
                    best_thr = t.threat_factor;
                    hpt = Some(t.id);
                }
            }
        }
        self.hpt_id = hpt;
    }

    pub fn run_behavior(&mut self) {
        match self.behavior {
            Behavior::External => {}
            Behavior::Duck => {
                self.fsm = FsmState::Search;
                self.hdg_cmd = heading_to(self.pos, self.target_pos);
                self.level_cmd = self.target_pos[1];
                self.g_cmd = 1.0;
                self.fire_cmd = false;
            }
            Behavior::Baseline1 => self.run_baseline1(),
        }
    }

    fn run_baseline1(&mut self) {
        let d_shot = self.beh.d_shot.first().copied().unwrap_or(0.85);
        let l_crank = self.beh.l_crank.first().copied().unwrap_or(0.6);
        let l_break = self.beh.l_break.first().copied().unwrap_or(0.95);

        let hpt = self
            .hpt_id
            .and_then(|id| self.enemy_tracks.iter().find(|t| t.id == id && t.detected))
            .cloned();

        if let Some(ref t) = hpt {
            if t.threat_factor >= l_break {
                self.fsm = FsmState::Evade;
                let side = if t.aspect >= 0.0 { 1.0 } else { -1.0 };
                self.hdg_cmd = clamp_hdg(self.hdg + 90.0 * side);
                self.g_cmd = self.max_g * 0.8;
                self.fire_cmd = false;
                return;
            }
        }

        if self.supporting_missile {
            self.fsm = FsmState::MissileSupport;
            if let Some(ref t) = hpt {
                let bearing = clamp_hdg(self.hdg + t.aspect);
                let side = if t.aspect >= 0.0 { 1.0 } else { -1.0 };
                self.hdg_cmd = clamp_hdg(bearing + 50.0 * side);
                self.g_cmd = 3.0;
            }
            self.fire_cmd = false;
            return;
        }

        if let Some(ref t) = hpt {
            self.fsm = FsmState::Engage;
            let bearing = clamp_hdg(self.hdg + t.aspect);
            if t.offensive_factor <= l_crank {
                let side = if t.aspect >= 0.0 { 1.0 } else { -1.0 };
                self.hdg_cmd = clamp_hdg(bearing + 40.0 * side);
            } else {
                self.hdg_cmd = bearing;
            }
            self.g_cmd = 4.0;
            let range_ratio = t.dist / t.own_wez.r_max.max(1e-6);
            self.fire_cmd = range_ratio <= d_shot && t.aspect.abs() < 30.0 && self.missiles > 0;
            return;
        }

        self.fsm = FsmState::Search;
        self.hdg_cmd = heading_to(self.pos, self.target_pos);
        self.level_cmd = self.target_pos[1];
        self.g_cmd = 1.5;
        self.fire_cmd = false;
    }

    pub fn physics_tick(&mut self, dt: f64) {
        if !self.alive {
            return;
        }
        self.dist2go = distance2d(self.pos, self.target_pos);

        let hdg_diff = clamp_hdg(self.hdg_cmd - self.hdg);
        let g_lim = self
            .g_cmd
            .clamp(1.0, self.max_g * Self::altitude_g_factor(self.pos[1]));
        let turn_rate_deg = (g_lim * SConv::GRAVITY_GDM / self.speed.max(1e-3)).to_degrees();
        let step = hdg_diff.clamp(-turn_rate_deg * dt, turn_rate_deg * dt);
        self.hdg = clamp_hdg(self.hdg + step);

        let level_diff = self.level_cmd - self.pos[1];
        let desired_pitch = level_diff.clamp(-15.0, 35.0);
        self.pitch += (desired_pitch - self.pitch).clamp(-0.5, 0.5);

        self.speed = self.max_speed * Self::altitude_speed_factor(self.pos[1]);
        let rad = self.hdg.to_radians();
        self.pos[0] += rad.sin() * self.speed * dt;
        self.pos[1] = (self.pos[1] + self.pitch.to_radians().sin() * self.speed * dt)
            .clamp(self.min_level, self.max_level);
        self.pos[2] += -rad.cos() * self.speed * dt;
    }

    pub fn build_obs(&self, allies: &[AircraftView]) -> StructuredObs {
        let brg_tgt = heading_to(self.pos, self.target_pos);
        let own = OwnObs {
            x: self.pos[0] / 3000.0,
            z: self.pos[2] / 3000.0,
            altitude: self.pos[1] / 150.0,
            dist_target: self.dist2go / 3000.0,
            aspect_to_target: aspect_angle(self.hdg, brg_tgt) / 180.0,
            heading: self.hdg / 180.0,
            speed: self.speed / self.max_speed,
            missiles: self.missiles as f64 / 6.0,
            supporting_missile: if self.supporting_missile { 1.0 } else { 0.0 },
        };

        let enemies = self
            .enemy_tracks
            .iter()
            .map(|t| {
                if t.detected {
                    let dist_target = allies
                        .iter()
                        .find(|a| a.id == t.id)
                        .map(|a| a.dist2go / 3000.0)
                        .unwrap_or(0.5);
                    // enemies are not in allies — use track only
                    let _ = dist_target;
                    EnemyObs {
                        id: t.id,
                        alt_diff: t.alt_diff,
                        aspect: t.aspect / 180.0,
                        angle_off: t.angle_off / 180.0,
                        dist: t.dist / 3000.0,
                        dist_target: 0.5,
                        own_r_max: t.own_wez.r_max / 926.0,
                        own_r_nez: t.own_wez.r_nez / 926.0,
                        enemy_r_max: t.enemy_wez.r_max / 926.0,
                        enemy_r_nez: t.enemy_wez.r_nez / 926.0,
                        threat_factor: t.threat_factor - 1.0,
                        offensive_factor: t.offensive_factor - 1.0,
                        is_missile_support: if t.is_missile_support { 1.0 } else { 0.0 },
                        detected: 1.0,
                    }
                } else {
                    EnemyObs {
                        id: t.id,
                        alt_diff: 0.0,
                        aspect: aspect_angle(self.hdg, 0.0) / 180.0,
                        angle_off: 0.0,
                        dist: -1.0,
                        dist_target: 0.5,
                        own_r_max: 0.0,
                        own_r_nez: 0.0,
                        enemy_r_max: 0.0,
                        enemy_r_nez: 0.0,
                        threat_factor: 0.0,
                        offensive_factor: 0.0,
                        is_missile_support: 0.0,
                        detected: 0.0,
                    }
                }
            })
            .collect();

        let ally_obs = self
            .ally_ids
            .iter()
            .map(|aid| {
                if let Some(a) = allies.iter().find(|x| x.id == *aid) {
                    if a.alive && self.share_tracks {
                        let dist = distance2d(self.pos, a.pos);
                        let brg = heading_to(self.pos, a.pos);
                        AllyObs {
                            id: *aid,
                            alt_diff: (self.pos[1] - a.pos[1]) / 150.0,
                            aspect: aspect_angle(self.hdg, brg) / 180.0,
                            angle_off: angle_off(self.hdg, a.hdg) / 180.0,
                            dist: dist / 3000.0,
                            dist_target: a.dist2go / 3000.0,
                            detected: 1.0,
                        }
                    } else {
                        AllyObs {
                            id: *aid,
                            alt_diff: 0.0,
                            aspect: aspect_angle(self.hdg, 0.0) / 180.0,
                            angle_off: 0.0,
                            dist: -1.0,
                            dist_target: 0.5,
                            detected: 0.0,
                        }
                    }
                } else {
                    AllyObs {
                        id: *aid,
                        alt_diff: 0.0,
                        aspect: 0.0,
                        angle_off: 0.0,
                        dist: -1.0,
                        dist_target: 0.5,
                        detected: 0.0,
                    }
                }
            })
            .collect();

        StructuredObs {
            own,
            allies: ally_obs,
            enemies,
        }
    }
}
