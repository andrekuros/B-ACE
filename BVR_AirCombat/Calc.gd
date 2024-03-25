#Calculations Functions
class_name Calc

static func get_hdg_2d(from_pos, to_pos) -> float:
	var direction_vector = to_pos - from_pos
	var angle_radians = atan2( -direction_vector.x , -direction_vector.z,)			
	return clamp_hdg(rad_to_deg(angle_radians))


static func get_2d_aspect_angle(object_heading_deg: float, target_direction_deg: float) -> float:	
	return clamp_hdg(target_direction_deg - object_heading_deg)
	
static func get_2d_aspect_angle_from_objs(shooter, target):	
	return get_2d_aspect_angle(shooter.current_hdg, get_hdg_2d(shooter.position, target.position ))


static func get_2d_angle_off(shooter_hdg, target_hdg):
	return clamp_hdg(target_hdg - shooter_hdg)

static func get_3d_angle_off(shooter, target):	
	var shooter_to_target = (target.global_transform.origin - shooter.global_transform.origin).normalized()
	var shooter_forward = -shooter.global_transform.basis.z.normalized() # Assuming Z is forward	
		
	return rad_to_deg(acos(shooter_forward.dot(shooter_to_target)))# Convert radians to degrees_off

static func distance2D_to_pos(A, B):	
#	# Create new vectors that ignore the Y component
	var A_flat = Vector3(A.x, 0, A.z)
	var B_flat = Vector3(B.x, 0, B.z)	
	return A_flat.distance_to(B_flat)

	
static func get_desired_heading(current_hdg_deg, desired_relative_radial_deg):	
	return clamp_hdg(current_hdg_deg + desired_relative_radial_deg)

static func clamp_hdg(hdg):
	if hdg > 180.0:
		return hdg - 360.0
	elif hdg < -180.0:
		return hdg + 360.0
	else:
		return hdg

static func get_level_diff(shooter, target):
	var level_diff = target.global_transform.origin.y - shooter.global_transform.origin.y
	return level_diff
