extends CharacterBody3D

const missile = preload("res://missile.tscn")
const Track = preload("res://Figther_assets.gd").Track
const SConv = preload("res://Figther_assets.gd").SConv

@onready var env = get_tree().root.get_node("FlyBy")
@onready var tasksDoneViewer = env.get_node("CanvasLayer/Control/TasksDone")
@onready var actionsPanel = env.get_node("CanvasLayer/Control/ActionPanel")

# Assume you have a Missile scene set up with its own script for homing in on targets
var phy_fps = 20
var action_repeat = 10

# AIR COMBAT DATA
var team_id = 1 # Example: 1 or 2 for two different teams
var radar_range = 60.0 * SConv.NM2GDM  # Detection range for the radar
var enemies_in_range = [] # List to store detected enemies

var radar_fov = 45 # degrees
var radar_near_range = 10.0 * SConv.NM2GDM # minimum distance to detect
var radar_far_range = 60.0 * SConv.NM2GDM # maximum distance to detect

var missiles = 4 # Adjust the number of missiles as needed

var model = "Simple" 

# State variables
var current_speed: float = 550 * SConv.KNOT2GDM_S 
var throttle: float = 1.0  # Throttle position: 0.0 (idle) to 1.0 (full)
var bank_angle: float = 0.0  # Current bank angle
var current_hdg = 0.0

var	hdg_input: float = 0.0 
var	level_input: float = 20000 * SConv.FT2GDM 
var	speed_input: float = 650 * SConv.KNOT2GDM_S
var	desiredG_input: float = 0.0 
var	shoot_input: int = 0

var wing_area = 50
var max_speed = 650 * SConv.KNOT2GDM_S  # Example max speed value
var min_speed = 250 * SConv.KNOT2GDM_S # Example min speed value

var max_pitch = deg_to_rad(35.0)
var min_pitch = deg_to_rad(-15.0)
var pitch_speed = 1.0

var max_g = 9.0

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
var behaviour = "baseline1" # baseline1 / external
var AP_mode = "FlyHdg" #"GoTo" / "Hold"
var holdStatus = 0
var best_goal_distance := 10000.0
var transform_backup = null

#Simulations config
var n_steps = 0
const MAX_STEPS = 10 * 60 * 20
var needs_reset = false

var reward = 0.0
var kill_reward = 0.0
var killed_reward = 0.0
var shot_reward = 0.0
var miss_reward = 0.0

var activated = true

var material2 = null
var team_color = null

#Heuristic Behavior Params
var max_shoot_range = 35.0 * SConv.NM2GDM
var max_shoot_range_var = 0.1
var max_shoot_range_adjusted = -1

var tatic_status = "Search" #"MissileSupport / Commit / Evade / Recommit
var tatic_time = 0.0
var tatic_start = 0.0
var last_beh_proc = 0.0
var int_hdg = 0.0

var pitch_input  = 0.0
var turn_input = 0.0

var radar_track_list = {}
var HPT = -1
var data_link_list = []
var in_flight_missile = null

func is_type(type): return type == "Fighter" 
func get_type(): return "Fighter"	

func _ready():
	transform_backup = transform
	
	var root_node = $RenderModel/Sketchfab_model  # Adjust the path to your model's root node.	
	team_color = Color.BLUE if team_id == 1 else Color.RED  # Set the desired color.	
	change_mesh_instance_colors(root_node, team_color)
	reset()
	
func reset():
	needs_reset = false
	
	cur_goal = env.get_next_goal(null)
	transform_backup = transform_backup
	position = init_position
	
	#inertial_velocity = Vector3.ZERO
	velocity = Vector3(0,0,-max_speed * SConv.NM2GDM)
	#rotation = Vector3.ZERO	
	rotation_degrees = init_rotation#Vector3(0, 0, 0) # Adjust as necessary	
		
	hdg_input = init_rotation.y
	current_hdg = init_hdg
	
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
	tatic_time = 0.0	
	
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
		
	var tracks_info = []
	
	#var own_info = { "pos_x"     : global_transform.origin.x / 3000, 
					 #"pos_z"     : global_transform.origin.z / 3000,
					 #"altitude"  : global_transform.origin.y / 150.0,
					 #"heading"   : current_hdg / 180.0,
					 #"speed"     : current_speed / max_speed,
					 #"missiles"  : missiles / 4.0,
					 #"in_flight_missile": 1 if in_flight_missile != null else 0,										 
					#}
	
	
	var own_info = [ global_transform.origin.x / 3000,
					 global_transform.origin.z / 3000,
					 global_transform.origin.y / 150.0,
					 current_hdg / 180.0,
					 current_speed / max_speed,
					 missiles / 4.0,
					 1 if is_instance_valid(in_flight_missile) else 0
					]
		
	for track in radar_track_list.values():
		
		var info
		if track.activated:					
			info.append_array([ global_transform.origin.y / 150.0,
					 track.radial / 180.0,
					 track.dist,
					 1 if track.id == HPT else 0
					])
		else:			
			info.append_array([ 0.0, 0.0 , 0.0, 0.0 ])
		tracks_info.append_array(info)
	
	#print("bef:",  tracks_info, len(own_info))
	for track in range(2 - len(tracks_info)):
		tracks_info.append_array([ 0.0, 0.0 , 0.0, 0.0 ])
	#print( tracks_info, len(own_info))
	
	var obs = own_info + tracks_info
	#return {"obs": {"own_info": own_info, "tracks_info" : tracks_info}}	
	return {"observation": obs}

func update_reward():
	
	reward += kill_reward
	reward += shot_reward
	reward += miss_reward 
	
	#reward -= 0.01 # step penalty
	
	kill_reward = 0.0
	shot_reward = 0.0
	miss_reward = 0.0
	
	#reward += shaping_reward()

func get_reward():
	return reward
	
#func shaping_reward():
	#var s_reward = 0.0
	#var goal_distance = to_local(cur_goal.position).length()
	#if goal_distance < best_goal_distance:
		#s_reward += best_goal_distance - goal_distance
		#best_goal_distance = goal_distance
		#
	#s_reward /= 1.0
	#return s_reward 

func set_heuristic(heuristic):
	self._heuristic = heuristic

func get_obs_space():
	# typs of obs space: box, discrete, repeated
	return {
		"observation": {
			"size": [len(get_obs()["observation"])],
			"space": "box"
		}
	}   

func get_action_space():
	return {
		#"desiredG_input" : {
			#"size": 1,
			#"action_type": "continuous"
		#},    
		#"hdg_input" : {
			#"size" : 1,
			#"action_type" : "continuous"						
		#},    
		#"level_input" : {
			#"size": 1,
			#"action_type": "continuous"
		#} ,
		#"shoot_input" : {
			#"size": 1,
			#"action_type": "continuous"
		#}   
		#
		
		"input" : {
			"size": 4,
			"action_type": "continuous"
		}           		
		
		#"flyTo" : {		
			#"action_type": "discrete",						
			#"size": 100												
		#}				
		
	}

func set_action(action):
		
	##env.debug_text.add_text("\nAction:" + str(action)) 
	#hdg_input = action["hdg_input"] * 180.0		
	#level_input = (action["level_input"] * 22500.0 + 27500.0) * SConv.FT2GDM  	
	#desiredG_input = (action["desiredG_input"] * (max_g  - 1.0) + (max_g + 1.0))/2.0	
	#shoot_input = 0 if action["shoot_input"] <= 0 else 1
		
	hdg_input = action["input"][0] * 180.0		
	level_input = (action["input"][1] * 22500.0 + 27500.0) * SConv.FT2GDM  	
	desiredG_input = (action["input"][2] * (max_g  - 1.0) + (max_g + 1.0))/2.0	
	shoot_input = 0 if action["input"][3] <= 0 else 1
	
	if RenderingServer.render_loop_enabled: 
		if env.camera_global() == get_viewport().get_camera() or get_meta("id") == 0:			
			#env.debug_text.add_text("\nlevel_input:" + str(level_input)) 
			#env.debug_text.add_text("\nhdg_input:" + str(hdg_input)) 
			#env.debug_text.add_text("\ndesiredG_input:" + str(desiredG_input))
			#env.debug_text.add_text("\nShoot_input:" + str(shoot_input))
			
			actionsPanel.update_uav_data(action["input"], max_g)			
	
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
		
func process_behavior(delta_s):
		
	tatic_time += delta_s	
	
	if tatic_status == "Search" or tatic_status == "Return":
		
		if HPT != -1:				
			
			#Define new shotdistance with randominess
			max_shoot_range_adjusted = max_shoot_range  + randf_range(-max_shoot_range_var * max_shoot_range, max_shoot_range_var * max_shoot_range)						
			
			tatic_status = "Engage"        
			AP_mode = "FlyHdg"				
			desiredG_input = 3.0
			tatic_time = 0.0
			
		elif tatic_status == "Search":
			#Go back if achieved the midle of the arena
			if 	position.z >= 0:
				var oposite_hdg = rad_to_deg(global_transform.basis.get_euler().y) + 180.0				
				hdg_input = fmod(oposite_hdg + 180.0, 360.0) - 180.0
				desiredG_input = 3.0	
				tatic_status == "Return"							
				tatic_time = 0.0
			
		elif tatic_status == "Return" and tatic_time >= 80.0:			
			hdg_input = init_hdg
			desiredG_input = 3.0	
			tatic_status == "Search"							
			tatic_time = 0.0
			

	if tatic_status == "Engage":
		
		if HPT != -1:							
			#print(radar_track_list[HPT].dist, "Shot: ", max_shoot_range_adjusted)	
			hdg_input = fmod(radar_track_list[HPT].radial + current_hdg, 360) 
			#print("Hdg_target: ", hdg_input)
			
			if radar_track_list[HPT].dist < max_shoot_range_adjusted:
				if launch_missile_at_target(radar_track_list[HPT].obj): 
					tatic_status = "MissileSupport"			
					tatic_time = 0.0
					max_shoot_range_adjusted = -1
					#print(tatic_status, tatic_time)
		else:
			tatic_status = "Search"        
			AP_mode = "FlyHdg"				
			tatic_time = 0.0	
			#print(tatic_status, tatic_time)
			
		
	if tatic_status == "MissileSupport": 
		
		if is_instance_valid(in_flight_missile):			
			if in_flight_missile.pitbull or in_flight_missile == null:
			
				tatic_status = "Evade"        
				AP_mode = "FlyHdg"				
				tatic_time = 0.0		
								
				var oposite_hdg = rad_to_deg(global_transform.basis.get_euler().y) + 180.0				
				hdg_input = fmod(oposite_hdg + 180.0, 360.0) - 180.0
				desiredG_input = 6.0								
				#print(tatic_status, tatic_time, " / ", hdg_input)
		else:
			tatic_status = "Search"        
			AP_mode = "FlyHdg"				
			tatic_time = 0.0	
			#print(tatic_status, tatic_time)
			

	if tatic_status == "Evade" and tatic_time >= 50.0:
		
		tatic_status = "Search"		
		AP_mode = "FlyHdg"
		
		var oposite_hdg = rad_to_deg(global_transform.basis.get_euler().y) + 180				
		hdg_input = fmod(oposite_hdg + 180, 360) - 180
		desiredG_input = 3.0		
				
		tatic_time = 0.0		
		#print(tatic_status, tatic_time, " / ", hdg_input)
			
func remove_track(track_id):
	
	if HPT == track_id:
		HPT = -1
		if is_instance_valid(in_flight_missile):			
			if not in_flight_missile.pitbull and in_flight_missile != null:
				in_flight_missile.lost_support()
				in_flight_missile = null
				miss_reward -= 1.0
				
	if radar_track_list.has(track_id):
		radar_track_list[track_id].detected_status(false)
		
func _physics_process(delta: float) -> void:

	current_hdg = rad_to_deg(global_transform.basis.get_euler().y)
	
	process_tracks()
	
	if n_steps % action_repeat == 0:
		if behaviour == "baseline1":			
			process_behavior(delta * (n_steps - last_beh_proc))
			last_beh_proc = n_steps
		
	if  behaviour == "external"  and shoot_input > 0:
		if launch_missile_at_target(radar_track_list[HPT].obj): 						
			shoot_input = -1.0			
	
	var turn_g = clamp(desiredG_input, desiredG_input,  max_g) * SConv.GRAVITY_GDM
	var turn_speed =  turn_g / velocity.length() 
	
	process_manouvers_action()
	
	# Rotate the transform based checked the input values
	transform.basis = transform.basis.rotated(transform.basis.x.normalized(), pitch_input * pitch_speed * delta)
	transform.basis = transform.basis.rotated(Vector3.UP, turn_input * turn_speed * delta)	
		
	$RenderModel.rotation.z = lerp($RenderModel.rotation.z, -float(turn_input) , turn_speed)
	$RenderModel.rotation.x = lerp($RenderModel.rotation.x, -float(pitch_input), turn_speed )

	# Movement is always forward
	velocity = -transform.basis.z.normalized() * max_speed
	# Handle landing/taking unchecked
	set_velocity(velocity)
	set_up_direction(Vector3.UP)
	move_and_slide()
	
	n_steps += 1
	
	if n_steps >= MAX_STEPS:
		done = true
	
	update_reward()
	
		
func zero_reward():
	reward = 0.0  
	
func process_behavior_actions():
	
	if shoot_input == 1:
		
		if max_shoot_range_adjusted == -1:
			max_shoot_range_adjusted = max_shoot_range  + randf_range(-max_shoot_range_var * max_shoot_range, max_shoot_range_var * max_shoot_range)
			
		#print(radar_track_list[HPT].dist, "Shot: ", max_shoot_range_adjusted)	
		if radar_track_list[HPT].dist < max_shoot_range_adjusted:
			if launch_missile_at_target(radar_track_list[HPT].obj): 
				#tatic_status = "MissileSupport"			
				#tatic_time = 0
				max_shoot_range_adjusted = -1
				#print(tatic_status, tatic_time)
		shoot_input = 0
			
func process_manouvers_action():
	#print(_heuristic)
	if _heuristic == "model":
		return
	
	#if _heuristic == "human":
		#turn_input = Input.get_action_strength("roll_left") - Input.get_action_strength("roll_right")
		#pitch_input = Input.get_action_strength("pitch_up") - Input.get_action_strength("pitch_down")
	#
	if _heuristic == "AP":		
		
		
		#if AP_mode == "GoTo": 
														#
			##print(targetHdg)
			#if goal_distance > 3:			
				#turn_input = (targetHdg / abs(1 if targetHdg == 0 else targetHdg)) * (0.85 + (clamp(20 / goal_distance, 0,1))) * clamp(abs(targetHdg), 0.0 , 1.0)  
				##if turn_input < 0.1:
				##	turn_input = 0.0
																#
		#
		if AP_mode == "FlyHdg":
			#-------- HDG Adjust ----------#
			# Calculate the heading difference between current and desired								
			var hdg_diff = hdg_input - current_hdg			
			# Normalize the heading difference to the range [-180, 180]
			hdg_diff = fmod(hdg_diff + 180, 360) - 180

			# Adjust turn sensitivity based on the heading difference magnitude					
			var adjusted_turn_input = hdg_diff / 5  
			turn_input = clamp(adjusted_turn_input, -1.0, 1.0)
#			
		# -------- Level Adjust ---------- #
		#
			var current_level = global_transform.origin.y
			var level_diff = level_input - current_level
			
			var adjusted_pitch_input = level_diff / 10			  
			
			var desired_pitch = clamp(adjusted_pitch_input, min_pitch, max_pitch)											
			var current_pitch = global_transform.basis.get_euler().x
			
			var pitch_diff = desired_pitch - current_pitch						
			pitch_input = pitch_diff
			
					
			#print("Level: ", level_diff, "PitchInput: ", pitch_input)
		
		#if AP_mode == "Hold":
			#
			#if holdStatus == 0:
				#if goal_distance > 10:			
					#turn_input = (targetHdg / abs(1 if targetHdg == 0 else targetHdg)) * (0.75 + (clamp(20 / goal_distance, 0,1))) * clamp(abs(targetHdg), 0.0 , 1.0)  				
				#else:
					#holdStatus = 1
			#elif holdStatus == 1:
				#if goal_distance < 50:
					#turn_input = 0
				#else:
					#holdStatus = 0	
				
func goal_reached(goal):
	
	if goal == cur_goal:
		reward += 100.0
				
		if goal.get_meta('id') != 0:
			env.goalsPending.remove_at(env.goalsPending.find(goal.get_meta('id')))
			#goal.visible = false		
			goal.material = goal.material2
			
			tasksDoneViewer.text = str(len(env.goalsPending)) + " / " + str(len(env.goals))
			
			#if len(env.goalsPending) == 0:
				#done = true
				#tasksDoneViewer.text = "ALL DONE"
												
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
	
#func exited_game_area():
	#done = true
	#reward -= 10.0
	#exited_arena = true
	#reset()

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
		
		env.add_child(new_missile)							
		new_missile.set_target(target) 
		new_missile.launch(velocity)			
		new_missile.shooter = self				
		new_missile.add_to_group("Missile")
		new_missile.global_position = global_position
			
		in_flight_missile = new_missile
								
		missiles -= 1		
		shot_reward += 0.1
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
	done = true	
	reward += -20.0
		
func reactivate():
		# Enabling processing
	set_process(true)
	set_physics_process(true)	
	collision_layer = init_layer
	collision_mask = init_mask
	input_ray_pickable = true	
	visible = true
	activated = true
	



#func update_transform(delta: float) -> void:
	## Apply bank (roll)
	#rotation_degrees.z = bank_angle
#
	## Apply pitch
	#rotation_degrees.x += pitch_input * turn_speed * delta
#
	## Forward movement
	#var forward_dir = transform.basis.z.normalized()
	#linear_velocity = forward_dir * current_speed
#
	## Update global position based on velocity
	#global_translate(linear_velocity * delta)


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
