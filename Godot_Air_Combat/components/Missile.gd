extends CharacterBody3D

const SConv = preload("res://assets/Sim_assets.gd").SConv
const Calc = preload("res://assets/Calc.gd")

var target: Node3D
var max_speed: float = 10.0 #3600 km/h
var ref_speed: float
# 'scalar_velocity' is available via velocity.length() if needed

var turn_speed: float = 2.0

var last_know_target
var last_know_velocity	
var direction_to_target
# var current_velocity # No longer needed, can use velocity.normalized() directly

var n_steps = 0

var max_time_of_flight: float = 50.0
var time_of_fligth: float = 0.0

var shooter = null
var missile_track = null
var upLink_support = true
var pitbull = false

const visual_scaleVector = Vector3(2.0, 2.0, 2.0)
var min_offset = Vector3(0.0001, 0.0001, 0.0001)

func is_type(type): return type == "Missile"
func get_type(): return "Missile"

func _ready():
	# No need to set gravity_scale = 0, CharacterBody3D doesn't have gravity by default.
	pass
	
func launch(_shooter, _target_track):
	set_shooter(_shooter)
	set_target(_target_track.obj)
	missile_track = _target_track
	
	get_node("RenderModel").set_scale(_shooter.get_node("RenderModel").get_scale()/2)
	
	last_know_target = _target_track.obj.global_transform.origin
	
	var shooter_linear_velocity = shooter.velocity
	
	var rotation_axis = shooter_linear_velocity.cross(Vector3.UP)
	if rotation_axis.length_squared() < 0.0001:
		rotation_axis = Vector3.RIGHT
	rotation_axis = rotation_axis.normalized()
	
	var direction_vector = target.global_transform.origin - shooter.global_transform.origin
	var pitch_angle = atan2(direction_vector.y, direction_vector.length()) * 180.0 / PI
	
	var missile_linear_velocity = shooter_linear_velocity.rotated(rotation_axis, deg_to_rad(45.0 + pitch_angle))
	
	# Set the initial velocity for the CharacterBody
	velocity = missile_linear_velocity
	look_at(global_transform.origin + velocity + min_offset, Vector3.UP)
	
	ref_speed = velocity.length()
	upLink_support = true
	
	$Timer.wait_time = max_time_of_flight
	$Timer.start()

func _physics_process(delta: float) -> void:
	time_of_fligth += delta
	
	if target:
		if pitbull or upLink_support:
			last_know_target = target.global_transform.origin
			last_know_velocity = target.velocity # Assuming target also has a velocity property
		else:
			last_know_target = last_know_target + last_know_velocity * delta
		
		direction_to_target = (last_know_target - global_transform.origin).normalized()
		var current_velocity_normalized = velocity.normalized()

		turn_speed = 0.1 + 5.0 * (1 - exp(-0.02 * (time_of_fligth)))
		var vertical_factor = min((1 + -current_velocity_normalized.y * 2.0 * turn_speed/5.0), 1.39)
		
		if time_of_fligth > 0.0:
			var new_direction: Vector3 = current_velocity_normalized.lerp(direction_to_target, turn_speed * delta)
			
			if ref_speed < max_speed:
				ref_speed += delta * 20.0
			
			var new_velocity: Vector3 = new_direction.normalized() * ref_speed * vertical_factor * vertical_factor
			
			# The new way to move a CharacterBody3D
			velocity = new_velocity
			move_and_slide()
			
		if n_steps % 10 == 0:
			var target_distance = global_position.distance_to(target.global_position)
			
			if target_distance < 10 * SConv.NM2GDM and not pitbull and upLink_support:
				pitbull = true
	
	if velocity.length_squared() > 0.01:
		look_at(global_transform.origin + velocity + min_offset, Vector3.UP)
		
	n_steps += 1

# Note: Your collision detection using an Area3D will continue to work perfectly.
# The _on_area_3d_body_entered function does not need to change at all.
func _on_area_3d_body_entered(body):
	if body.is_type("Fighter") and body != shooter:
		if body.activated:
			body.own_kill()
			shooter.ownRewards.add_hit_enemy_rew()
		queue_free()

# Other functions remain the same
func set_target(new_target: Node3D) -> void:
	target = new_target

func set_shooter(_shooter: Node3D) -> void:
	shooter = _shooter

func lost_support():
	upLink_support = false

func recover_support():
	upLink_support = true

func _on_timer_timeout():
	shooter.inform_missile_miss(self)
	queue_free()

func update_scale(_factor):
	var current_scale = get_node("RenderModel").get_scale()
	get_node("RenderModel").set_scale(current_scale * _factor)
