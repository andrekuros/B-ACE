extends CharacterBody3D

const missile = preload("res://missile.tscn")
const Track   = preload("res://Figther_assets.gd").Track
const SConv   = preload("res://Figther_assets.gd").SConv
const RewardsControl = preload("res://Figther_assets.gd").RewardsControl

const Calc = preload("res://Calc.gd")

var ownRewards = RewardsControl.new(self)

@onready var env = get_tree().root.get_node("FlyBy")
@onready var tasksDoneViewer = env.get_node("CanvasLayer/Control/TasksDone")
@onready var sync = get_tree().root.get_node("FlyBy/Sync")
#@onready var actionsPanel = env.get_node("CanvasLayer/Control/ActionPanel")

var alliesList = []
# Assume you have a Missile scene set up with its own script for homing in on targets
var phy_fps = 20
var action_repeat = 20

# AIR COMBAT DATA
var team_id = 1 # Example: 1 or 2 for two different teams
var radar_range = 60.0 * SConv.NM2GDM  # Detection range for the radar
var enemies_in_range = [] # List to store detected enemies

var radar_fov = 45 # degrees
var radar_near_range = 10.0 * SConv.NM2GDM # minimum distance to detect
var radar_far_range = 60.0 * SConv.NM2GDM # maximum distance to detect

var fullView = true

var missiles = 6 # Adjust the number of missiles as needed

var model = "Simple" 

# State variables
var current_speed: float = 550 * SConv.KNOT2GDM_S 
var throttle: float = 1.0  # Throttle position: 0.0 (idle) to 1.0 (full)
var bank_angle: float = 0.0  # Current bank angle
var current_hdg = 0.0

@export var action_type = "Low_Level_Discrete"# "Low_Level_Discrete" 

var	hdg_input: float = 0.0 
var	level_input: float = 20000 * SConv.FT2GDM 
var	speed_input: float = 650 * SConv.KNOT2GDM_S
var	desiredG_input: float = 0.0 
var	shoot_input: int = 0

var g_conv = [6.0, 3.0, 1.0, 3.0, 6.0]
var turn_conv = [-45.0, -20.0, 0.0, 20.0, 45.0]
var level_conv = [10, 45, 80, 115, 150]

var last_hdg_input = hdg_input
var last_level_input = level_input
var last_desiredG_input = desiredG_input
var last_fire_input = shoot_input

var wing_area = 50
var max_speed = 650 * SConv.KNOT2GDM_S # Example max speed value
var min_speed = 250 * SConv.KNOT2GDM_S # Example min speed value

var max_pitch = deg_to_rad(35.0)
var min_pitch = deg_to_rad(-15.0)
var pitch_speed = 0.5

var max_g = 9.0

var init_position = Vector3.ZERO
var init_rotation = Vector3.ZERO
var init_layer = collision_layer
var init_mask = collision_mask 
var init_hdg = 0
var dist2go = 100000.0

var target_position = Vector3.ZERO

var found_goal = false
var exited_arena = false
var cur_goal = null

var done = false
var _heuristic = "AP" #"model" / "AP"
var behaviour = "baseline1" # baseline1 / external
var AP_mode = "FlyHdg" #"GoTo" / "Hold"
var holdStatus = 0
var best_goal_distance := 10000.0
var goal_position = Vector3.ZERO

var transform_backup = null


#Simulations config
var n_steps = 0
const MAX_STEPS = 15 * 60 * 20
var needs_reset = false

var activated = true
var killed = false

var material2 = null
var team_color = null
var color_group = null

#Heuristic Behavior Params
var max_shoot_range = 30.0 * SConv.NM2GDM
var max_shoot_range_var = 0.1
var max_shoot_range_adjusted = -1
var defense_side = 1

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

# Maximum number of points to retain in the trail
var max_trail_points: int = 120 # Adjust based on desired trail length and update rate

var len_tracks_data_obs = 2
var len_allieds_data_obs = 2


func is_type(type): return type == "Fighter" 
func get_type(): return "Fighter"	

func _ready():
	transform_backup = transform
	
	var root_node = $RenderModel  # Adjust the path to your model's root node.	
	team_color = Color.BLUE if team_id == 1 else Color.RED  # Set the desired color.			
	color_group = "blue" if team_id == 1 else "red"	
		
	
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
	last_hdg_input = hdg_input
	current_hdg = init_hdg
	
	n_steps = 0
	found_goal = false
	exited_arena = false 
	done = false
	best_goal_distance = to_local(cur_goal.position).length()
	
	missiles = 6
	radar_track_list = {}	
		
	AP_mode = "FlyHdg" #"GoTo" / "Hold"
	holdStatus = 0
	best_goal_distance = 10000.0	
	dist2go = 100000.0
	
	ownRewards.get_total_rewards_and_reset()
	
	activated = true
	killed = false

	tatic_status = "Search" #"MissileSupport / Commit / Evade / Recommit
	tatic_time = 0.0	
	
	radar_track_list = {}
	HPT = -1
	data_link_list = {}
	in_flight_missile = null

	alliesList = []
	for agent in env.get_tree().get_nodes_in_group(color_group):
		if agent.get_meta("id") != get_meta("id"):
			alliesList.append(agent)  	
	
			
	len_allieds_data_obs = 1 if len(alliesList) >= 1 else 0
	len_tracks_data_obs = 2 if len(sync.env.get_tree().get_nodes_in_group("ENEMY")) > 1 else 1
	
	$Radar/CollisionShape3D.disabled = true    
	await(0.05)
	$Radar/CollisionShape3D.disabled = false  
	
	


#func reset_if_done():
	#if done:
		#reset()
		
func get_done():
	return done
	
func set_done_false():
	done = false
	
func get_obs(with_labels = false):
		
	var tracks_info = []
	
	var own_info = [ global_transform.origin.x / 3000.0,
					 global_transform.origin.z / 3000.0,
					 global_transform.origin.y / 150.0,
					 dist2go / 3000.0,
					 #fmod(aspect_to_obj(target_position) + current_hdg, 360),
					 Calc.get_relative_radial(current_hdg, Calc.get_hdg_2d(position, target_position)) / 180.0,
					 current_hdg / 180.0,
					 current_speed / max_speed,
					 missiles / 6.0,
					 1 if is_instance_valid(in_flight_missile) else 0,
					 last_desiredG_input,
					 last_hdg_input,
					 last_level_input,
					 last_fire_input,										
					]	
	var allied_info = [ 0.0, 0.0 , 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0 ]
	
	if len_allieds_data_obs > 0:
		var allied = alliesList[0]
		if allied.activated:
			allied_info = [  allied.global_transform.origin.x / 3000.0,
							 allied.global_transform.origin.z / 3000.0,
							 allied.global_transform.origin.y / 150.0,
							 allied.dist2go / 3000.0,							 
							 Calc.get_relative_radial(allied.current_hdg, Calc.get_hdg_2d(allied.position, allied.target_position)) / 180.0, 
							#fmod(aspect_to_obj(allied.target_position) + allied.current_hdg, 360),
							 allied.current_hdg / 180.0,
							 allied.current_speed / max_speed,
							 allied.missiles / 6.0,							 
							 1 if is_instance_valid(allied.in_flight_missile) else 0,
			]			
	
	for track in radar_track_list.values():
				
		#var info 
		#if track.detected:					
		var info = [ global_transform.origin.y / 150.0,
					 Calc.get_desired_heading(current_hdg, track.radial) / 180.0,
					 track.dist / 3000.0,
					 track.obj.dist2go / 3000.0,
					 1 if track.id == HPT else 0,
					 1 if track.detected else 0
				]
		#else:			
		#	info = [ 0.0, 0.0 , 0.0, 0.0, 0.0 ]
		tracks_info.append_array(info)
	
	#print("bef:",  tracks_info, len(own_info))
	
	for track in range(len_tracks_data_obs - len(tracks_info)/5):
		tracks_info.append_array([ 0.0, 0.0 , 0.0, 0.0, 0.0 , 0.0 ])
	#print( tracks_info, len(own_info))
	
	var obs = own_info + tracks_info 
	
	if len_allieds_data_obs > 0:
		obs += allied_info
	
	#return {"obs": {"own_info": own_info, "tracks_info" : tracks_info}}	
	if not with_labels:
		return {"observation": obs}
	else:
		var labels_own = ['pos_x', 'pos_z', 'alt', 'dist2go' ,'radial2go', 'hdg', 'speed', 'missiles', 'fly_mis', 
					  'last_g', 'last_hdg', 'last_level', ' last_fire_input' ]
		var labels_allied = ['DL_pos_x', 'DL_pos_z', 'DL_alt', 'DL_dist2go', 'DL_radial2go', 'DL_hdg', 'DL_speed', 'DL_missiles', 'DL_fly_mis']
		var labels_t1 = ['t1_alt', 't1_rad', 't1_dist', 'dist2go', 't1_hpt', 't1_active']
		var labels_t2 = ['t2_alt', 't2_rad', 't2_dist', 'dist2go', 't2_hpt', 't2_active']		
		
		var labels = labels_own
		if len_allieds_data_obs > 0:
			labels += labels_allied 
		
		if len_tracks_data_obs == 2:
			labels += labels_t1 + labels_t2		
		else:
			labels += labels_t1 
		
		return {"observation": obs, "labels": labels}

func get_reward():	
	return ownRewards.get_total_rewards_and_reset()
	
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
	
	if action_type == "Low_Level_Continuous":
	
		return {				
			"input" : {
				"size": 4,
				"action_type": "continuous"
			} 
		} 
	elif action_type == "Low_Level_Discrete":         		
		
		return {									
					"fire_input" : {
					"size": 1,
					"action_type": "discrete"
				},					
					"level_input" : {
					"size": 5,
					"action_type": "discrete"
				},
					"turn_input" : {
					"size": 5,
					"action_type": "discrete"
				},
				
		} 
	else:
		print("Fighter::Error::Unknown Action Type -> ", action_type)
		return {}			
			
func set_action(action):
			
	if action_type == "Low_Level_Continuous":
	
		last_hdg_input = action["input"][0]
		last_level_input = action["input"][1]
		last_desiredG_input = action["input"][2]
		last_fire_input = action["input"][3]
			
		hdg_input = Calc.get_desired_heading(current_hdg, last_hdg_input * 180.0)		
		level_input = (last_level_input * 22500.0 + 27500.0) * SConv.FT2GDM  	
		desiredG_input = (last_desiredG_input * (max_g  - 1.0) + (max_g + 1.0))/2.0	
		shoot_input = 0 if last_fire_input <= 0 else 1
	
	elif action_type == "Low_Level_Discrete":  
			
		last_hdg_input 		= action["turn_input"] 
		last_desiredG_input = g_conv[action["turn_input"]] 
		last_level_input 	= action["level_input"] 
		last_fire_input 	= action["fire_input"] 
			
		hdg_input = Calc.get_desired_heading(current_hdg, turn_conv[last_hdg_input])		
		level_input = level_conv[last_level_input]
		desiredG_input = last_desiredG_input
		shoot_input = last_fire_input   


func get_current_inputs():
	return [hdg_input, level_input, desiredG_input, shoot_input]
	
func process_tracks():	
	
	var min_dist = 100000
	var new_HPT = null
	
	#print("process_track")
	for id in radar_track_list.keys():
		var track = radar_track_list[id]							
		
		if track.detected or fullView:
						
			if track.obj.activated == false:
				track.detected = false						
				continue
			
			#var radial = fmod(aspect_to_obj(track.obj.position) + current_hdg, 360)
			var radial = Calc.get_hdg_2d(position, track.obj.position)
			var dist = to_local(track.obj.position).length()			
			track.update_dist_radial(dist, radial)			
			
			if dist < min_dist: # and track.obj.get_meta('id') == 1:
				min_dist = dist
				new_HPT = id
				
							
			#print("own_id: ", get_meta('id'), " t_td", track.id, " track_dist: ", dist, " rad:", radial)
	if HPT == -1 and new_HPT != null:
		HPT = new_HPT
		#print("HPT_set ", get_meta('id') , " - ", HPT)
		
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
			#Aproach the target
			#if 	position.z >= 0:
				#var oposite_hdg =  rad_to_deg(global_transform.basis.get_euler().y) + 180.0				
				#hdg_input = fmod(oposite_hdg + 180.0, 360.0) - 180.0
				#desiredG_input = 3.0	
				#tatic_status == "Return"							
				#tatic_time = 0.0
			
			if 	team_id == 0 and position.z >= 150 or\
				team_id == 1 and position.z <= -150:
				
				desiredG_input = 3.0	
				tatic_status = "Strike"							
				tatic_time = 0.0
				#print(tatic_status)
			
		elif tatic_status == "Return" and tatic_time >= 80.0:			
			hdg_input = init_hdg
			desiredG_input = 3.0	
			tatic_status = "Search"							
			tatic_time = 0.0
		
	if tatic_status == "Strike":						
		#hdg_input = fmod(aspect_to_obj(target_position) + current_hdg, 360) 
		hdg_input = Calc.get_hdg_2d(position, target_position )
		#print(hdg_input)
		

	if tatic_status == "Engage":
		
		if HPT != -1:							
			#print(radar_track_list[HPT].dist, "Shot: ", max_shoot_range_adjusted)	
			hdg_input = radar_track_list[HPT].radial
			
			#print("Hdg_target: ", hdg_input)
			
			if radar_track_list[HPT].dist < max_shoot_range_adjusted:
				if abs(Calc.get_relative_radial(current_hdg, radar_track_list[HPT].radial)) < 15:					
					if launch_missile_at_target(radar_track_list[HPT].obj): 
						tatic_status = "MissileSupport"			
						tatic_time = 0.0
						max_shoot_range_adjusted = -1
						defense_side = 1 - randi_range(0,1) * 2 #Choose defence side
						#print(tatic_status, tatic_time)							
			
			if 	team_id == 0 and position.z >= 150 or\
				team_id == 1 and position.z <= -150:
				
				desiredG_input = 3.0	
				tatic_status = "Strike"							
				tatic_time = 0.0
				#print(tatic_status)
		else:
			#tatic_status = "Search"        
			#AP_mode = "FlyHdg"
			#hdg_input = init_hdg				
			tatic_time = 0.0	
			#print(tatic_status, tatic_time)
			tatic_status = "Evade"        
			AP_mode = "FlyHdg"				
			tatic_time = 0.0		
								
				#var oposite_hdg = rad_to_deg(global_transform.basis.get_euler().y) + 180.0				
			hdg_input = Calc.clamp_hdg(current_hdg + 180)#fmod(oposite_hdg + 180.0, 360.0) - 180.0
			desiredG_input = 6.0								
			#print("ID:", get_meta("id"), ":" ,tatic_status, tatic_time, " / ", hdg_input)
			
		
	if tatic_status == "MissileSupport": 
		
		if is_instance_valid(in_flight_missile):			
			if in_flight_missile.pitbull or in_flight_missile == null:
			
				tatic_status = "Evade"        
				AP_mode = "FlyHdg"				
				tatic_time = 0.0		
								
				#var oposite_hdg = rad_to_deg(global_transform.basis.get_euler().y) + 180.0				
				hdg_input = Calc.clamp_hdg(current_hdg + 180- defense_side * 45.0)#fmod(oposite_hdg + 180.0, 360.0) - 180.0
				desiredG_input = 6.0								
				#print(tatic_status, tatic_time, " / ", hdg_input)
			else:
				if HPT != -1:
					hdg_input = Calc.clamp_hdg(radar_track_list[HPT].radial + defense_side * 45.0) 
				
				
		else:
			#tatic_status = "Search"        
			#AP_mode = "FlyHdg"				
			#tatic_time = 0.0	
			
			tatic_status = "Evade"        
			AP_mode = "FlyHdg"				
			tatic_time = 0.0		
								
				#var oposite_hdg = rad_to_deg(global_transform.basis.get_euler().y) + 180.0				
			hdg_input = Calc.clamp_hdg(current_hdg + 180- defense_side * 45.0)#fmod(oposite_hdg + 180.0, 360.0) - 180.0
			desiredG_input = 6.0			
			#print(tatic_status, tatic_time)
			

	if tatic_status == "Evade" and tatic_time >= 50.0:
		
		tatic_status = "Search"		
		AP_mode = "FlyHdg"
		
		hdg_input = Calc.clamp_hdg(current_hdg + 180)				
		#hdg_input = fmod(oposite_hdg + 180, 360) - 180
		desiredG_input = 3.0		
				
		tatic_time = 0.0		
		#print(tatic_status, tatic_time, " / ", hdg_input)
			
func remove_track(track_id):
	
	if HPT == track_id:
		HPT = -1
		if is_instance_valid(in_flight_missile):			
			if not in_flight_missile.pitbull and in_flight_missile != null:
				in_flight_missile.lost_support()
				#in_flight_missile = null
				#ownRewards.add_missile_miss_rew()
		#print("Figther(%s): Track Removed (%s)", get_meta("id"), track_id)
		#print("Fighter(%s): Track Removed (%s)"%[get_meta("id"), track_id])

	if radar_track_list.has(track_id):
		radar_track_list[track_id].detected_status(false)
		ownRewards.add_detect_loss_rew()
		
func reacquired_track(track_id, radial, dist):
	
	var track = radar_track_list[track_id]
	track.update_dist_radial(dist, radial)
	track.detected_status(true)
	
	if is_instance_valid(in_flight_missile):			
		if not in_flight_missile.pitbull and in_flight_missile != null:
			in_flight_missile.recover_support()			
				

		
func _physics_process(delta: float) -> void:

	current_hdg = rad_to_deg(global_transform.basis.get_euler().y)
	
	process_tracks()
	
	if n_steps % action_repeat == 0:
		if behaviour == "baseline1":			
			#if get_meta("id") == 2:
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
			var hdg_diff = Calc.clamp_hdg(hdg_input - current_hdg)	
			
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

#func exited_game_area():
	#done = true
	#reward -= 10.0
	#exited_arena = true
	#reset()
									

func launch_missile_at_target(target):
		
	if missiles > 0 and target:
		var new_missile = missile.instantiate()
		change_mesh_instance_colors(new_missile, team_color)
		
		env.add_child(new_missile)							
		#new_missile.set_target(target) 		
		#new_missile.set_shooter(self)				
		new_missile.add_to_group("Missile")
		new_missile.global_position = global_position
		
		new_missile.launch(self, target)			
			
		#There are already a missile in flight this missile lost support
		if is_instance_valid(in_flight_missile):			
			if not in_flight_missile.pitbull and in_flight_missile != null:
				in_flight_missile.lost_support()				
				ownRewards.add_missile_miss_rew()
		
		in_flight_missile = new_missile
								
		missiles -= 1		
		ownRewards.add_missile_fire_rew()
		return true
	else:
		ownRewards.add_missile_no_fire_rew()
		return false

func own_kill():
	if activated == true:
		set_process(false)
		set_physics_process(false)	
		collision_layer = 0
		collision_mask = 0
		input_ray_pickable = false	
		visible = false
		activated = false
		killed = true	
		done = true	
		ownRewards.add_hit_own_rew()
		
		if is_in_group("AGENT"):
			sync.agents_alive_control -= 1
		elif is_in_group("ENEMY"):
			sync.enemies_alive_control -= 1
		else:
			print("Figther::Warning::Agent in unknown Group -> ", get_groups())
	

		
func reactivate():
		# Enabling processing
	set_process(true)
	set_physics_process(true)	
	collision_layer = init_layer
	collision_mask = init_mask
	input_ray_pickable = true	
	visible = true
	activated = true
	killed = true
	ownRewards.get_total_rewards_and_reset()
	missiles = 6
	
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


