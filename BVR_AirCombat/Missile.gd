extends RigidBody3D

const SConv = preload("res://Sim_assets.gd").SConv
const Calc = preload("res://Calc.gd")

var target: Node3D
var max_speed: float = 10.0 #3600 km/h
var ref_speed: float
var scalar_velocity: float 

var turn_speed: float = 2.0

	

var pitbull = false
var n_steps = 0

var max_time_of_flight: float = 50.0 
var time_of_fligth: float =  0.0

var shooter = null
var upLink_support = true

const visual_scaleVector = Vector3(2.0,  2.0,  2.0)

func is_type(type): return type == "Missile" 
func get_type(): return "Missile"	

#func get_turn_speed_fator():
#	$Timer.time_left

func _ready():
	pass
	# Set the missile's initial velocity			
	
		
# Function to be called when launching the missile, passing the launcher's velocity
func launch(_shooter, _target):
		
	set_shooter(_shooter)
	set_target(_target)
	
	get_node("RenderModel").set_scale(_shooter.get_node("RenderModel").get_scale()/2)
	
	var radial_factor = abs(Calc.get_2d_aspect_angle_from_objs(_shooter, _target) / 180.0)
	var level_factor  = (_shooter.global_transform.origin.y - _target.global_transform.origin.y) / 150.0
	
	#max_time_of_flight = max_time_of_flight * (1 - 0.5 * radial_factor) #lost 50% 180deg fire
	#speed = speed * (1 + 0.3 * level_factor) #gain 30% speed with 45000ft diff 	

	# Get the shooter's linear velocity
	var shooter_linear_velocity = shooter.velocity	
	
	var rotation_axis = shooter_linear_velocity.cross(Vector3.UP)	
	if rotation_axis.length_squared() < 0.0001:
		rotation_axis = Vector3.RIGHT
	rotation_axis = rotation_axis.normalized()
	
	var direction_vector = target.global_transform.origin - shooter.global_transform.origin
	#var pitch_angle = (atan2(-direction_vector.z, -direction_vector.y)) * 180.0 / PI - 90
	var pitch_angle = atan2(direction_vector.y, direction_vector.length()) * 180.0 / PI
				
	
	#pitch_angle = -45.0
	# Rotate the shooter's linear velocity by 30 degrees around the rotation axis
	var missile_linear_velocity = shooter_linear_velocity.rotated(rotation_axis, deg_to_rad(45.0 + pitch_angle))
	#var upward_velocity = Vector3.UP * 0 # Adjust this value as needed
	
	
	# Set the missile's linear velocity
	linear_velocity = missile_linear_velocity 
	#linear_velocity += upward_velocity
	look_at(global_transform.origin + linear_velocity, Vector3.UP)			
	ref_speed = linear_velocity.length() 		
	
	upLink_support = true
	
	$Timer.wait_time = max_time_of_flight
	$Timer.start()


func _integrate_forces(state: PhysicsDirectBodyState3D) -> void:	
	time_of_fligth += state.step
	
	if target:
		var direction_to_target: Vector3 = (target.global_transform.origin - global_transform.origin).normalized()		
		var current_velocity: Vector3 = linear_velocity.normalized()
		scalar_velocity = linear_velocity.length()

		turn_speed = 0.1 + 5.0 * (1 - exp(-0.02* (time_of_fligth))) #get_turn_speed_fator()
		var vertical_factor = min((1 + -current_velocity.y * 2.0 * turn_speed/5.0), 1.3)
		#print(turn_speed)		
		if time_of_fligth > 0.0:
			var new_direction: Vector3 = current_velocity.lerp(direction_to_target, 1.0 * turn_speed * get_physics_process_delta_time())
			
			
			#print(vertical_factor)
			#vertical_component = 0.0
			#print((1 + vertical_component * turn_speed/5.0))
			
			if ref_speed < max_speed:
				ref_speed += state.step * 2.0
			#else:
			#	print(time_of_fligth, " REf:", ref_speed)			
			
			#print(ref_speed)
			var new_velocity: Vector3 = new_direction * (ref_speed) * vertical_factor * vertical_factor	
			
			linear_velocity = new_velocity			
					
				
		# Update the missile's velocity to move towards the target.
		if true:#time_of_fligth < 15.0:
			var initial_thust_force = -global_transform.basis.z * 130  / (turn_speed)#*turn_speed)#/ turn_speed*turn_speed#* 150 / time_of_fligth
			apply_central_force(initial_thust_force)
			#print(initial_thust_force)
			#linear_velocity = new_velocity	+ upward_velocity			
		#else:
		#	linear_velocity = new_velocity	
		#print(scalar_velocity)
		if n_steps % 10 == 0:
			var target_vector = to_local(target.position)
			var target_distance = target_vector.length()
			#print(target_distance)
			if target_distance < 10 * SConv.NM2GDM and not pitbull:
				pitbull = true
				#print("Pitbull")
		
		#if linear_velocity.length() > 0.01 and (upLink_support or pitbull):
	look_at(global_transform.origin + linear_velocity, Vector3.UP)
	
	n_steps += 1

	
func set_target(new_target: Node3D) -> void:
	target = new_target

func set_shooter(_shooter: Node3D) -> void:
	shooter = _shooter

func lost_support():	
	upLink_support = false
	#queue_free()

func recover_support():	
	upLink_support = true

func _on_timer_timeout():
	#print("missile: MISS ")	
	queue_free()  # Remove the missile from the scene


func _on_area_3d_body_entered(body):	
	if body.is_type("Fighter") and body != shooter: 	
		# Implement what happens when the missile hits a target				
		if body.activated:
			body.own_kill()		
			#Reward of hitting enemy
			shooter.ownRewards.add_hit_enemy_rew()
			# Remove the missile from the scene
		#print(time_of_fligth)
		queue_free() 
		
func update_scale(_factor):
	var current_scale =get_node("RenderModel").get_scale()
	get_node("RenderModel").set_scale(current_scale * _factor)
