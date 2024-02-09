extends CharacterBody3D


const missile = preload("res://missile.tscn")
const Track = preload("res://Figther_assets.gd").Track

const SConv = preload("res://Figther_assets.gd").SConv

# Maximum airspeed
var max_flight_speed = 650 * SConv.KNOT2GDM_S#REAL [KNos] | SIM [M/S]

# Turn rate
@export var turn_speed = 1.0
@export var level_speed = 12.0
#@export var turn_acc = 4.0
@onready var env = get_tree().root.get_node("FlyBy")

@onready var tasksDoneViewer = env.get_node("CanvasLayer/Control/TasksDone")
# Assume you have a Missile scene set up with its own script for homing in on targets


# AIR COMBAT DATA
var team_id = 1 # Example: 1 or 2 for two different teams
var radar_range = 60.0 * SConv.NM2GDM  # Detection range for the radar
var enemies_in_range = [] # List to store detected enemies

var radar_fov = 45 # degrees
var radar_near_range = 10.0 * SConv.NM2GDM # minimum distance to detect
var radar_far_range = 60.0 * SConv.NM2GDM # maximum distance to detect

var missiles = 4 # Adjust the number of missiles as needed

var model = "Simple" 
var pitch_speed = 2.0
#var throttle_delta = 30
var acceleration = 6.0
var forward_speed = 650 * SConv.KNOT2GDM_S
var target_speed = 650 *  SConv.KNOT2GDM_S
var turn_input = 0

# State variables
var current_speed: float = 0.0
var throttle: float = 0.0  # Throttle position: 0.0 (idle) to 1.0 (full)
var bank_angle: float = 0.0  # Current bank angle
var pitch_input: float = 0.0  # Pitch control input
var roll_input: float = 0.0  # Roll control input
var linear_velocity: Vector3  = Vector3.ZERO

## Flight parameters
var deceleration: float = 5.0
var max_bank_angle: float = 45.0  # Maximum bank angle in degrees
var lift_factor: float = 0.4
var gravity_effect: float = -9.8
var drag_factor: float = 0.05

var init_position = Vector3.ZERO
var init_rotation = Vector3.ZERO
var init_layer = collision_layer
var init_mask = collision_mask 
var init_hdg = 0

var found_goal = false
var exited_arena = false
var cur_goal = null

var done = false
var _heuristic = "AP" #"model" / "AP"
var AP_mode = "FlyHdg" #"GoTo" / "Hold"
var holdStatus = 0
var best_goal_distance := 10000.0
var transform_backup = null

#Simulations config
var n_steps = 0
const MAX_STEPS = 200000
var needs_reset = false
var reward = 0.0
var activated = true

var material2 = null
var team_color = null

#Heuristic Behavior Params
var max_shoot_range = 40 * SConv.NM2GDM
var max_shoot_range_var = 0.1
var max_shoot_range_adjusted = -1

var tatic_status = "Search" #"MissileSupport / Commit / Evade / Recommit
var tatic_time = 0
var int_hdg = 0
var desired_hdg = 0

var radar_track_list = {}
var HPT = -1
var data_link_list = []
var in_flight_missile = null

func is_type(type): return type == "Fighter" 
func    get_type(): return "Fighter"		

func _ready():
	transform_backup = transform
	
	var root_node = $RenderModel/Sketchfab_model  # Adjust the path to your model's root node.	
	team_color = Color.BLUE if team_id == 1 else Color.RED  # Set the desired color.	
	change_mesh_instance_colors(root_node, team_color)

		
func reset():
	needs_reset = false
	
	cur_goal = env.get_next_goal(null)
	transform_backup = transform_backup
	position = init_position
	
	velocity = Vector3.ZERO
	#rotation = Vector3.ZERO	
	rotation_degrees = init_rotation#Vector3(0, 0, 0) # Adjust as necessary	
		
	desired_hdg = init_rotation.y
	
	n_steps = 0
	found_goal = false
	exited_arena = false 
	done = false
	best_goal_distance = to_local(cur_goal.position).length()
	
	missiles = 4
	radar_track_list = {}	
		
	AP_mode = "FlyHdg" #"GoTo" / "Hold"
	holdStatus = 0
	best_goal_distance = 10000.0	

	#Simulations config
	reward = 0.0
	activated = true

	tatic_status = "Search" #"MissileSupport / Commit / Evade / Recommit
	tatic_time = 0
	
	radar_track_list = {}
	HPT = -1
	data_link_list = {}
	in_flight_missile = null
	
	$Radar/CollisionPolygon3D.disabled = true    
	await(0.01)
	$Radar/CollisionPolygon3D.disabled = false    
	
	# reset position, orientation, velocity

#func reset_if_done():
	#if done:
		#reset()
		
func get_done():
	return done
	
func set_done_false():
	done = false
	
func get_obs():
	
	
	##var goal_vector = (cur_goal.position - position).normalized() # global frame of reference
	#var goal_vector = to_local(cur_goal.position)
	#var goal_distance = goal_vector.length()
	#goal_vector = goal_vector.normalized()
	#goal_distance = clamp(goal_distance, 0.0, 50.0)
	#
	#var next_goal = env.get_next_goal(cur_goal)
	#var next_goal_vector = to_local(next_goal.position)
	#var next_goal_distance = next_goal_vector.length()
	#next_goal_vector = next_goal_vector.normalized()
	#next_goal_distance = clamp(next_goal_distance, 0.0, 50.0)  

	var obs = [
		missiles,
		len(radar_track_list),
		activated,
		needs_reset		
	]
	
	return {"obs":obs}

func update_reward():
	reward -= 0.01 # step penalty
	reward += shaping_reward()

func get_reward():
	return reward
	
func shaping_reward():
	var s_reward = 0.0
	var goal_distance = to_local(cur_goal.position).length()
	if goal_distance < best_goal_distance:
		s_reward += best_goal_distance - goal_distance
		best_goal_distance = goal_distance
		
	s_reward /= 1.0
	return s_reward 

func set_heuristic(heuristic):
	self._heuristic = heuristic

func get_obs_space():
	# typs of obs space: box, discrete, repeated
	return {
		"obs": {
			"size": [len(get_obs()["obs"])],
			"space": "box"
	}
	}   

func get_action_space():
	return {
		"turn" : {
			"size": 1,
			"action_type": "continuous"
		},        
		"pitch" : {
		"size": 1,
			"action_type": "continuous"
		},        		
		#"flyTo" : {		
			#"action_type": "discrete",						
			#"size": 100												
		#}				
		
	}

func set_action(action):
	turn_input = action["turn"][0]
	pitch_input = action["pitch"][0]
	
	#env.debug_text.add_text("\nAction:" + str(action)) 

func process_tracks():	
	
	var min_dist = 100000
	var new_HPT = null
	
	#print("process_track")
	for id in radar_track_list.keys():
		var track = radar_track_list[id]							
		
		if track.detected:
						
			if track.obj.activated == false:
				track.detected = false						
				continue
			
			var radial = aspect_to_obj(track.obj)
			var dist = to_local(track.obj.position).length()			
			track.update_dist_radial(dist, radial)			
			
			if dist < min_dist:
				min_dist = dist
				new_HPT = id
							
			#print("own_id: ", get_meta('id'), " t_td", track.id, " track_dist: ", dist, " rad:", radial)
	if HPT == -1 and new_HPT != null:
		HPT = new_HPT
		#print("HPT_set", HPT)
		
func process_behavior():
	
	tatic_time += 1
		
	if tatic_status == "MissileSupport": 
		
		if is_instance_valid(in_flight_missile):
			if in_flight_missile.pitbull or in_flight_missile == null:
			
				tatic_status = "Evade"        
				AP_mode = "FlyHdg"
				tatic_time = 0		
				
				var oposite_hdg = rad_to_deg(global_transform.basis.get_euler().y) + 180				
				desired_hdg = fmod(oposite_hdg + 180, 360) - 180								
				#print(tatic_status, tatic_time, " / ", desired_hdg)			

	if tatic_status == "Evade" and tatic_time >= 10:
		
		tatic_status = "Search"		
		AP_mode == "FlyHdg"
		
		var oposite_hdg = rad_to_deg(global_transform.basis.get_euler().y) + 180				
		desired_hdg = fmod(oposite_hdg + 180, 360) - 180		
				
		tatic_time = 0		
		#print(tatic_status, tatic_time, " / ", desired_hdg)
			
	if tatic_status == "Search":# and team_id != 0:		
		if HPT != -1:	
			
			if max_shoot_range_adjusted == -1:
				max_shoot_range_adjusted = max_shoot_range  + randf_range(-max_shoot_range_var * max_shoot_range, max_shoot_range_var * max_shoot_range)
			
			#print(radar_track_list[HPT].dist, "Shot: ", max_shoot_range_adjusted)	
			if radar_track_list[HPT].dist < max_shoot_range_adjusted:
				if launch_missile_at_target(radar_track_list[HPT].obj): 
					tatic_status = "MissileSupport"			
					tatic_time = 0
					max_shoot_range_adjusted = -1
					#print(tatic_status, tatic_time)

func remove_track(track_id):
	
	if HPT == track_id:
		HPT = -1
	if radar_track_list.has(track_id):
		radar_track_list[track_id].detected_status(false)


func _physics_process(delta):
		
	if n_steps % 20 == 0:
		process_tracks()		
	
	if n_steps % 20 == 0:		
		process_behavior()				
	
	if n_steps >= MAX_STEPS:
		done = true
		needs_reset = true

	if needs_reset:
		reset()
		return

	if cur_goal == null:
		reset()
	
	set_input()
	
	if false:
		handle_controls(delta)
		apply_physics(delta)
		update_transform(delta)
		
	else:
		## Rotate the transform based checked the input values
		transform.basis = transform.basis.rotated(transform.basis.x.normalized(), pitch_input * pitch_speed * delta)
		transform.basis = transform.basis.rotated(Vector3.UP, turn_input * turn_speed * delta)	
				
		$RenderModel.rotation.z = lerp($RenderModel.rotation.z, -float(turn_input), turn_speed * delta)
		$RenderModel.rotation.x = lerp($RenderModel.rotation.x, -float(pitch_input), level_speed * delta)#
		
		## Movement is always forward
		velocity = -transform.basis.z.normalized() * max_flight_speed
		
		set_velocity(velocity)
		set_up_direction(Vector3.UP)
		move_and_slide()
		
	update_reward()
	n_steps += 1
		
func zero_reward():
	reward = 0.0  
	
func set_input():
	#print(_heuristic)
	if _heuristic == "model":
		return
	
	if _heuristic == "human":
		turn_input = Input.get_action_strength("roll_left") - Input.get_action_strength("roll_right")
		pitch_input = Input.get_action_strength("pitch_up") - Input.get_action_strength("pitch_down")
	
	if _heuristic == "AP":		
		var targetHdg = aspect_to_obj(cur_goal)									
		var goal_vector = to_local(cur_goal.position)
		var goal_distance = goal_vector.length()
		
		if AP_mode == "GoTo": 
														
			#print(targetHdg)
			if goal_distance > 3:			
				turn_input = (targetHdg / abs(1 if targetHdg == 0 else targetHdg)) * (0.85 + (clamp(20 / goal_distance, 0,1))) * clamp(abs(targetHdg), 0.0 , 1.0)  
				#if turn_input < 0.1:
				#	turn_input = 0.0
																
		
		if AP_mode == "FlyHdg":
			# Calculate the heading difference between current and desired
			var current_hdg = rad_to_deg(global_transform.basis.get_euler().y)
			#print(current_hdg , " ;; ",desired_hdg)
			
			var hdg_diff = desired_hdg - current_hdg
			# Normalize the heading difference to the range [-180, 180]
			hdg_diff = fmod(hdg_diff + 180, 360) - 180

			# Adjust turn sensitivity based on the heading difference magnitude
			var turn_sensitivity = 10.0  # Adjust this value based on your game's mechanics or aircraft's capabilities
			var adjusted_turn_input = hdg_diff * turn_sensitivity / 180  # Assuming full input over a 180-degree turn

			# Determine turn input based on the shortest direction to turn, clamped to [-1, 1]
			turn_input = clamp(adjusted_turn_input, -1, 1)

		
		if AP_mode == "Hold":
			
			if holdStatus == 0:
				if goal_distance > 10:			
					turn_input = (targetHdg / abs(1 if targetHdg == 0 else targetHdg)) * (0.75 + (clamp(20 / goal_distance, 0,1))) * clamp(abs(targetHdg), 0.0 , 1.0)  				
				else:
					holdStatus = 1
			elif holdStatus == 1:
				if goal_distance < 50:
					turn_input = 0
				else:
					holdStatus = 0	
				
func goal_reached(goal):
	
	if goal == cur_goal:
		reward += 100.0
				
		if goal.get_meta('id') != 0:
			env.goalsPending.remove_at(env.goalsPending.find(goal.get_meta('id')))
			#goal.visible = false		
			goal.material = goal.material2
			
			tasksDoneViewer.text = str(len(env.goalsPending)) + " / " + str(len(env.goals))
			
			if len(env.goalsPending) == 0:
				done = true
				tasksDoneViewer.text = "ALL DONE"
								
				
		#print("Next Target")
		cur_goal = null#env.get_next_goal(cur_goal)
		if len(env.goals) > 1:
			
			var auxGoals = env.goalsPending.duplicate()
			
			while cur_goal == null and len(auxGoals) > 0: 
				
				var randIndex = env.rng.randi_range(0,len(auxGoals)-1)
				var index_nextGoal = auxGoals[randIndex]
				auxGoals.remove_at(randIndex)
				#print(index_nextGoal)
				if env.goals[index_nextGoal][1] == -1:
					cur_goal = env.goals[index_nextGoal][0]
					env.goals[index_nextGoal][1] = get_meta('id')
					break	
			if len(auxGoals) == 0:
				cur_goal = env.goals[0][0]
				AP_mode = "Hold"
				#print("Mode == Hold")					
		else:
			cur_goal = env.goals[0][0]
			AP_mode = "Hold"
			#print("Mode == Hold")
	
func exited_game_area():
	done = true
	reward -= 10.0
	exited_arena = true
	reset()

#Kur Functions
func aspect_to_obj(obj):
		#var hdg  = (vec1 - vec2).normalized()	
	#var rad = Vector2($PlaneModel.global_position.x, $PlaneModel.global_position.z).angle_to(Vector2(obj.global_position.x, obj.global_position.z))	
	#var hdg = $PlaneModel.global_transform.basis.get_euler().y
	var hdgO = 0;
	var goal_vector = to_local(obj.position)
	
	if goal_vector.x != 0:
		hdgO  = Vector2(goal_vector.x, goal_vector.z).angle_to(Vector2.UP)	
		#print(hdgO)
		return rad_to_deg(hdgO)
	
	return 0.0
	#print(rad_to_deg(rad))#rad_to_deg($PlaneModel.global_transform.basis.get_euler().y))
	#print(rad * 57.8, " ||||| " ,hdg * 57.8, "  --- ", rad_to_deg(rad - hdg))
									

func launch_missile_at_target(target):
		
	if missiles > 0 and target:
		var new_missile = missile.instantiate()
		change_mesh_instance_colors(new_missile, team_color)
		
		#new_missile.global_transform = global_transform	
		new_missile.global_position = global_position
		
		new_missile.set_target(target) 
		new_missile.launch(linear_velocity)			
		new_missile.shooter = self
		
		env.add_child(new_missile)
		
		in_flight_missile = new_missile
								
		missiles -= 1
		#print("shot")
		return true
	else:
		return false


func kill():
	set_process(false)
	set_physics_process(false)	
	collision_layer = 0
	collision_mask = 0
	input_ray_pickable = false	
	visible = false
	activated = false
		
func reactivate():
		# Enabling processing
	set_process(true)
	set_physics_process(true)	
	collision_layer = init_layer
	collision_mask = init_mask
	input_ray_pickable = true	
	visible = true
	activated = true

	
#--------------- Physics ----------------#


func handle_controls(delta: float) -> void:
	# Basic control inputs (adapt as needed for your control scheme)
	throttle = clamp(throttle + Input.get_action_strength("throttle_up") - Input.get_action_strength("throttle_down"), 0.0, 1.0)
	roll_input = Input.get_action_strength("turn_right") - Input.get_action_strength("turn_left")
	pitch_input = Input.get_action_strength("pitch_down") - Input.get_action_strength("pitch_up")

	# Adjust bank angle based on roll input
	bank_angle = lerp(bank_angle, roll_input * max_bank_angle, delta * turn_speed)

func apply_physics(delta: float) -> void:
	# Speed control
	var target_speed = throttle * max_flight_speed
	current_speed += clamp(target_speed - current_speed, -deceleration * delta, acceleration * delta)

	# Drag
	current_speed = max(0.0, current_speed - (current_speed * drag_factor * delta))

	# Lift reduction based on bank angle
	var effective_lift = cos(deg_to_rad(bank_angle)) * lift_factor - gravity_effect
	# Apply effective lift
	linear_velocity.y += effective_lift * delta

func update_transform(delta: float) -> void:
	# Apply bank (roll)
	rotation_degrees.z = bank_angle

	# Apply pitch
	rotation_degrees.x += pitch_input * turn_speed * delta

	# Forward movement
	var forward_dir = transform.basis.z.normalized()
	linear_velocity = forward_dir * current_speed

	# Update global position based on velocity
	global_translate(linear_velocity * delta)




# Recursively traverses the node tree to find MeshInstance nodes and changes their material color.
func change_mesh_instance_colors(node: Node, new_color: Color) -> void:
	# Iterate through all children of the current node.
	for child in node.get_children():
		# If a child is a MeshInstance, process it.
		if child is MeshInstance3D:
			# Assuming the MeshInstance uses a material that can have its color changed (e.g., SpatialMaterial in Godot 3.x, StandardMaterial3D in Godot 4.x).
			for material_index in range(child.get_surface_override_material_count()):
				var material = child.get_surface_override_material(material_index)
				if material:
					var new_material = material.duplicate()  # Duplicate to avoid changing the original material used elsewhere.
					if "albedo_color" in new_material:  # Check if the material has the 'albedo_color' property.
						new_material.albedo_color = new_color						
					child.set_surface_override_material(material_index, new_material)
		# If a child is not a MeshInstance but might have children of its own, recursively search its subtree.
		change_mesh_instance_colors(child, new_color)

	# Recursively call this function for all children of the current node.
	for child in node.get_children():
		change_mesh_instance_colors(child, new_color)




