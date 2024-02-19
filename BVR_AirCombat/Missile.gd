extends RigidBody3D

const SConv = preload("res://Figther_assets.gd").SConv

var target: Node3D
var speed: float = 150.0 #* SConv.KNOT2GDM_S
var turn_speed: float = 2.0

var time_of_flight: float = 35.0 
var pitbull = false

var initial_velocity: Vector3
var n_steps = 0

var shooter = null


func is_type(type): return type == "Missile" 
func    get_type(): return "Missile"		


func _ready():
	# Set the missile's initial velocity
	linear_velocity = initial_velocity
	# Additional setup for the missile's independent flight path
	$Timer.wait_time = time_of_flight
	$Timer.start()
	

# Function to be called when launching the missile, passing the launcher's velocity
func launch(launcher_velocity: Vector3):
	initial_velocity = launcher_velocity
	# Add the missile to the scene, set its global position, etc.

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

		# Optionally, ensure the missile is always facing towards its movement direction.
		if linear_velocity.length() > 0.01:
			look_at(global_transform.origin + linear_velocity, Vector3.UP)
	
	n_steps += 1

func set_target(new_target: Node3D) -> void:
	target = new_target

func lost_support():
	queue_free()
	

func _on_area_3d_area_entered(area):
	
	var body = area.get_parent()	
	if body.is_type("Fighter") and body != shooter: 	
		# Implement what happens when the missile hits a target
		var id = body.get_meta("id")
		var own_id = shooter.get_meta("id")		
		#print("missile: Hit " , own_id, " -> ",id)
		#body.remove_from_group("AGENT")
		body.kill()
		
		shooter.kill_reward += 5.0
		#body.visible = false
		
		queue_free() # Remove the missile from the scene
	#else:
		#print("notTarget")


func _on_timer_timeout():
	#print("missile: MISS ")
	queue_free()  # Remove the missile from the scene




