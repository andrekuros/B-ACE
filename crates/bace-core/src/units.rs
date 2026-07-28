//! Unit conversions for B-ACE 2.0.
//! Positions use Godot-equivalent meters (GDM): real meters / 100.

pub struct SConv;

impl SConv {
    pub const SCALE_FACTOR: f64 = 100.0;
    pub const REAL2GD: f64 = 1.0 / Self::SCALE_FACTOR;
    pub const NM2M: f64 = 1852.0;
    pub const NM2GDM: f64 = 1852.0 / Self::SCALE_FACTOR;
    pub const KNOT2M_S: f64 = 1.0 / 1.944;
    pub const KNOT2GDM_S: f64 = 1.0 / (1.944 * Self::SCALE_FACTOR);
    pub const GDM2NM: f64 = Self::SCALE_FACTOR / 1852.0;
    pub const GDM_S2KNOT: f64 = 1.944 * Self::SCALE_FACTOR;
    pub const FT2M: f64 = 0.3048;
    pub const FT2GDM: f64 = 0.3048 / Self::SCALE_FACTOR;
    pub const GRAVITY_GDM: f64 = 9.81 * Self::REAL2GD;
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn nm_conversion_roundtrip() {
        let nm = 50.0;
        let gdm = nm * SConv::NM2GDM;
        assert!((gdm * SConv::GDM2NM - nm).abs() < 1e-9);
    }
}
