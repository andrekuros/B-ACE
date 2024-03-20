extends RigidBody3D

const SConv = preload("res://Sim_assets.gd").SConv
const Calc = preload("res://Calc.gd")

var target: Node3D
var speed: float = 75.0 #* SConv.KNOT2GDM_S
var turn_speed: float = 2.0

var time_of_flight: float = 60.0 
var pitbull = false

var initial_velocity: Vector3
var n_steps = 0

var shooter = null
var upLink_support = true

const visual_scaleVector = Vector3(2.0,  2.0,  2.0)

func is_type(type): return type == "Missile" 
func get_type(): return "Missile"		


func _ready():
	# Set the missile's initial velocity
	linear_velocity = initial_velocity
	# Additional setup for the missile's independent flight path
	
	get_node("RenderModel").set_scale(visual_scaleVector)
	$Timer.wait_time = time_of_flight
	$Timer.start()
	
# Function to be called when launching the missile, passing the launcher's velocity
func launch(_shooter, _target):
		
	set_shooter(_shooter)
	set_target(_target)
	
	var radial_factor = abs(Calc.get_2d_angle_off(_shooter, _target) / 180.0)
	var level_factor  = (_shooter.global_transform.origin.y - _target.global_transform.origin.y) / 150.0
	
	time_of_flight = time_of_flight * (1 - 0.5 * radial_factor) #lost 50% 180deg fire
	speed = speed * (1 + 0.3 * level_factor) #gain 30% speed with 45000ft diff 	
	
	initial_velocity = shooter.velocity	
	upLink_support = true
	

func _integrate_forces(state: PhysicsDirectBodyState3D) -> void:	
	if target:
		var direction_to_target: Vector3 = (target.global_transform.origin - global_transform.origin).normalized()		
		var current_velocity: Vector3 = linear_velocity.normalized()
		var new_velocity: Vector3 = current_velocity.lerp(direction_to_target * speed, turn_speed * get_physics_process_delta_time())
				
		# Update the missile's velocity to move towards the target.
		linear_velocity = new_velocity				
		
		if n_steps % 10 == 0:
			var target_vector = to_local(target.position)
			var target_distance = target_vector.length()
			#print(target_distance)
			if target_distance < 10 * SConv.NM2GDM and not pitbull:
				pitbull = true
				#print("Pitbull")
		
		if linear_velocity.length() > 0.01 and (upLink_support or pitbull):
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
		queue_free() 
