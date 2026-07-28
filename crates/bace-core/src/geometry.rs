//! Geometry helpers for headings and aspect angles.

/// Clamp heading into (-180, 180].
pub fn clamp_hdg(hdg: f64) -> f64 {
    let mut h = ((hdg + 180.0) % 360.0 + 360.0) % 360.0 - 180.0;
    if h <= -180.0 {
        h += 360.0;
    }
    h
}

/// Desired absolute heading from current heading and normalized delta in [-1, 1] (= ±180°).
pub fn desired_heading(current_hdg: f64, normalized_delta: f64) -> f64 {
    clamp_hdg(current_hdg + normalized_delta * 180.0)
}

/// 2D heading from `from` toward `to` (degrees, Godot-style: 0 = +Z north-ish).
/// Uses XZ plane: heading 0 looks along -Z (matching Godot fighter forward).
pub fn heading_to(from: [f64; 3], to: [f64; 3]) -> f64 {
    let dx = to[0] - from[0];
    let dz = to[2] - from[2];
    // Godot: hdg = rad_to_deg(-atan2(dx, -dz)) style — use atan2(dx, -dz)
    let hdg = dx.atan2(-dz).to_degrees();
    clamp_hdg(hdg)
}

/// Aspect angle of target relative to own heading (-180..180).
pub fn aspect_angle(own_hdg: f64, bearing_to_target: f64) -> f64 {
    clamp_hdg(bearing_to_target - own_hdg)
}

/// Angle-off: difference between own heading and target heading.
pub fn angle_off(own_hdg: f64, target_hdg: f64) -> f64 {
    clamp_hdg(target_hdg - own_hdg)
}

/// Horizontal distance in XZ plane.
pub fn distance2d(a: [f64; 3], b: [f64; 3]) -> f64 {
    let dx = a[0] - b[0];
    let dz = a[2] - b[2];
    (dx * dx + dz * dz).sqrt()
}

/// 3D distance.
pub fn distance3d(a: [f64; 3], b: [f64; 3]) -> f64 {
    let dx = a[0] - b[0];
    let dy = a[1] - b[1];
    let dz = a[2] - b[2];
    (dx * dx + dy * dy + dz * dz).sqrt()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn clamp_wraps() {
        assert!((clamp_hdg(190.0) - (-170.0)).abs() < 1e-9);
        assert!((clamp_hdg(-190.0) - 170.0).abs() < 1e-9);
        assert!((clamp_hdg(0.0)).abs() < 1e-9);
    }

    #[test]
    fn distance_xz() {
        let a = [0.0, 10.0, 0.0];
        let b = [3.0, 99.0, 4.0];
        assert!((distance2d(a, b) - 5.0).abs() < 1e-9);
    }
}
