//! Redesigned WEZ model for B-ACE 2.0.
//!
//! Geometric engagement envelope (not the legacy Godot Expression polynomials).
//! RMax / RNez depend on shooter altitude, aspect, and angle-off.

use crate::units::SConv;

/// Weapon engagement zone estimate in GDM.
#[derive(Debug, Clone, Copy)]
pub struct WezRanges {
    pub r_max: f64,
    pub r_nez: f64,
}

/// Evaluate WEZ for a shooter against a target geometry.
///
/// Inputs:
/// - `shooter_alt_gdm`: altitude in GDM
/// - `aspect_deg`: aspect angle of target from shooter
/// - `angle_off_deg`: heading difference
pub fn evaluate(shooter_alt_gdm: f64, aspect_deg: f64, angle_off_deg: f64) -> WezRanges {
    // Base ranges at 25k ft reference (~76.2 GDM)
    let alt_ft = shooter_alt_gdm / SConv::FT2GDM;
    let alt_factor = (0.6 + 0.4 * (alt_ft / 25000.0).clamp(0.2, 1.5)).clamp(0.4, 1.4);

    let aspect = aspect_deg.to_radians().abs();
    let aoff = angle_off_deg.to_radians().abs();

    // Head-on aspect improves RMax; beam/tail reduces it.
    let aspect_factor = (1.15 - 0.55 * (aspect / std::f64::consts::PI)).clamp(0.35, 1.2);
    let aoff_factor = (1.05 - 0.35 * (aoff / std::f64::consts::PI)).clamp(0.5, 1.1);

    let r_max_nm = 28.0 * alt_factor * aspect_factor * aoff_factor;
    let r_nez_nm = r_max_nm * (0.45 + 0.15 * aspect_factor);

    WezRanges {
        r_max: (r_max_nm * SConv::NM2GDM).max(0.01),
        r_nez: (r_nez_nm * SConv::NM2GDM).max(0.01),
    }
}

/// Threat / offensive factors used by FSM (range relative to envelopes).
pub fn offensive_factor(range_gdm: f64, own_r_max: f64, own_r_nez: f64) -> f64 {
    if range_gdm <= own_r_nez {
        2.0
    } else if range_gdm <= own_r_max {
        1.0 + (own_r_max - range_gdm) / (own_r_max - own_r_nez + 1e-6)
    } else {
        own_r_max / (range_gdm + 1e-6)
    }
}

pub fn threat_factor(range_gdm: f64, enemy_r_max: f64, enemy_r_nez: f64) -> f64 {
    offensive_factor(range_gdm, enemy_r_max, enemy_r_nez)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn head_on_longer_than_beam() {
        let head = evaluate(76.2, 0.0, 0.0);
        let beam = evaluate(76.2, 90.0, 90.0);
        assert!(head.r_max > beam.r_max);
        assert!(head.r_nez < head.r_max);
    }
}
