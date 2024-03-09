extends RigidBody3D

const SConv = preload("res://Figther_assets.gd").SConv

var target: Node3D
var speed: float = 150.0 # Assuming initial speed, you may adjust or remove based on thrust application
var turn_speed: float = 2.0
var thrust_acceleration: float = 30.0 # Initial acceleration due to thrust
var drag_coefficient: float = 0.1 # Simplified drag coefficient
var gravity_effect: float = 9.81 # Gravity effect, considering only for loft and dive adjustments

var time_of_flight: float = 35.0 
var pitbull = false

var initial_velocity: Vector3
var n_steps = 0

var shooter = null
var upLink_support = true
var flight_phase = "loft" # Possible values: "loft", "cruise", "dive"

func is_type(type): return type == "Missile" 
func get_type(): return "Missile"		

func _ready():
	linear_velocity = initial_velocity
	$Timer.wait_time = time_of_flight
	$Timer.start()

func launch(_shooter, _target):
		
	set_shooter(_shooter)
	set_target(_target)
	
	linear_velocity = shooter.velocity	
	upLink_support = true

func _integrate_forces(state: PhysicsDirectBodyState3D) -> void:	
	if target:
		var altitude = global_transform.origin.y
		var speed = linear_velocity.length()
		var drag = -drag_coefficient * speed * speed # Simplified drag force
		
		var thrust = 0.0
		if n_steps < time_of_flight / 4: 
			thrust = thrust_acceleration # Apply thrust only in the first quarter
		
		# Adjust velocity based on current flight phase and physics
		var acceleration = (thrust + drag) / mass - gravity_effect # Simplifying gravity's role
		linear_velocity += transform.basis.z.normalized() * acceleration * get_physics_process_delta_time()
		
		if pitbull or n_steps >= time_of_flight / 4:
			flight_phase = "dive" # Transition to dive phase post loft or based on other conditions
			var direction_to_target: Vector3 = (target.global_transform.origin - global_transform.origin).normalized()
			linear_velocity = linear_velocity.lerp(direction_to_target * speed, turn_speed * get_physics_process_delta_time())

		if linear_velocity.length() > 0.01 and (upLink_support or pitbull):
			look_at(global_transform.origin + linear_velocity, Vector3.UP)

	n_steps += 1

func set_target(new_target: Node3D) -> void:
	target = new_target

func set_shooter(_shooter: Node3D) -> void:
	shooter = _shooter

func lost_support():	
	upLink_support = false

func recover_support():	
	upLink_support = true

func _on_area_3d_area_entered(area):
	var body = area.get_parent()	
	if body.is_type("Fighter") and body != shooter:	
		if body.activated:
			body.own_kill()		
			shooter.ownRewards.add_hit_enemy_rew()
		queue_free() 

func _on_timer_timeout():
	queue_free()
