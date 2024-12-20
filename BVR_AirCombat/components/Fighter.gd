extends CharacterBody3D

const missile = preload("res://components/missile.tscn")
const Track   = preload("res://assets/Sim_assets.gd").Track
const SConv   = preload("res://assets/Sim_assets.gd").SConv
const RewardsControl = preload("res://assets/Sim_assets.gd").RewardsControl
const Calc 	  = preload("res://assets/Calc.gd")
const Marker  = preload("res://assets/marker.tscn")

@onready var mainView = get_tree().root.get_node("B_ACE")

var trail_node: MeshInstance3D
var trail_mesh: ImmediateMesh
var trail_material: StandardMaterial3D
var trail_points = [] # Array to store the trail points
var max_trail_points: int = 180 * 4 # Adjust based on desired trail length and update rate
var trail_update_rate = 5 #Update the trail every 20 steps
var trail_color: Color = Color(1.0, 1.0, 1.0, 0.1) # Red color with 50% alpha
var trail_color_start: Color = Color(1.0, 1.0, 1.0, 0.0) # Starting color
var trail_color_end: Color = Color(1.0, 1.0, 1.0, 1.0) # Ending color (transparent)


#@onready var sync = get_tree().root.get_node("B_ACE/Sync")
var manager = null
var tree = null
var ownRewards = null
var max_cycles = -1
#@onready var actionsPanel = env.get_node("CanvasLayer/Control/ActionPanel")

var alliesList = []
var share_states = true
var share_tracks = true
# Assume you have a Missile scene set up with its own script for homing in on targets
var phy_fps
var action_repeat

# AIR COMBAT DATA
var team_id = 1 # Example: 0 or 1 for two different teams
var id
var agent_name
var radar_range = 50.0 * SConv.NM2GDM  # Detection range for the radar
var radar_hfov = [-60.0, 60.0] # degrees
var radar_vfov = [-20.0, 40.0] # degrees
var enemies_in_range = [] # List to store detected enemies

var fullView = false
var actions_2d = false

var missiles = 6 # Adjust the number of missiles as needed

var model = "Simple" 

# State variables
var current_time 
var current_speed
var current_level
var current_hdg
var current_pitch 

var action_type = "Low_Level_Discrete"# "Low_Level_Discrete" 

var	hdg_input: float = 0.0 
var	level_input: float = 25000 * SConv.FT2GDM 
var	desiredG_input: float = 1.0 
var	shoot_input: int = 0

var last_hdg_input
var last_level_input
var last_desiredG_input
var last_fire_input

var max_speed = 650 * SConv.KNOT2GDM_S
var max_level = 50000 * SConv.FT2GDM
var min_level = 1000  * SConv.FT2GDM

const max_g = 9.0

var max_pitch = 35.0
var min_pitch = -15.0
var pitch_speed = 0.5

func altitude_speed_factor (alt):
	return 0.2 * alt / 76.2 + 0.8 #25000ft is base alt for speed

func altitude_g_factor (alt):
	return -0.5 * alt / 76.2 + 1.5 #25000ft is base alt for max_g

var init_position = Vector3.ZERO
var init_rotation = Vector3.ZERO
var init_layer = collision_layer
var init_mask = collision_mask 
var init_hdg = 0
var dist2go = 100000.0
var strike_line_z = 0.0
var strike_line_xL = 0.0
var strike_line_xR = 0.0

var target_position = Vector3.ZERO

var done = false
var _heuristic = "AP" #"model" / "AP"
var behavior = "baseline1" # baseline1 / external
var mission = "DCA" #"striker"

var dShot 	= 0.85
var lCrank 	= 0.6
var lBreak	= 0.95

var dShotList 	= [0.85]
var lCrankList 	= [0.6]
var lBreakList	= [0.95]

var AP_mode = "FlyHdg" #"GoTo" / "Hold"

#Simulations config
var n_steps = 0
const MAX_STEPS = 15 * 60 * 20
var needs_reset = false

var activated = true
var killed = false

var team_color
var team_color_group

#Heuristic Behavior Params
#var max_shoot_range = 30 *  SConv.NM2GDM
var shoot_range_variation = 0.025
var shoot_range_error 	  = -1
var crank_variation		= 0.025
var crank_error 		= -1
var break_variation		= 0.025
var break_error		 	= -1

var defense_side = 1

var tatic_status = "Search" #"MissileSupport / Commit / Evade / Recommit
var sub_tatic = "None" #"Crank
var do_crank = false
var tatic_time = 0.0
var tatic_start = 0.0
var last_beh_proc = 0.0
var int_hdg = 0.0

var pitch_input  = 0.0
var turn_input = 0.0

var g_conv = [max_g, 3.0, 1.0, 3.0, max_g]
var turn_conv = [-45.0, -20.0, 0.0, 20.0, 45.0]
var level_conv = [10, 45, 80, 115, 150]

var action_g_len = len(g_conv)
var action_turn_len = len(turn_conv) 
var action_level_len = len(level_conv) 

var radar_track_list = []
var allied_track_list = []
var HPT 	= null
var HRT 	= null
var data_link_list = []
var in_flight_missile = null

var len_tracks_data_obs = 0
var len_allieds_data_obs = 0

var selected_obs_tracks  = []
var selected_obs_allieds = []

var test_executed = false

var simGroups
var init_config = null

var rMax_model
var rMax_calc

var rNez_model
var rNez_calc

var allied_info_null = [
	["allied_x_pos", 0.0],
	["allied_z_pos", 0.0],
	["allied_y_pos", 0.0],
	["allied_dist2go", 0.0],
	["allied_aspect_angle", 0.0],
	["allied_current_hdg", 0.0],
	["allied_current_speed", 0.0],
	["allied_missiles", 0.0],
	["allied_in_flight_missile", 0.0]
]


func is_type(type): return type == "Fighter" 
func get_type(): return "Fighter"	

func _ready():	
	#$Radar/CollisionShape3D.disabled = true 
	# Initialize trail_points and other configurations
	# Initialize trail_points and other configurations
	trail_points = []

	# Create the Trail node dynamically
	trail_node = MeshInstance3D.new()
	trail_node.transform = Transform3D.IDENTITY
	# Add the trail node to the scene tree
	get_parent().get_parent().add_child(trail_node)
			
	

func update_init_config(config, rewConfig = {}):
		
	init_config = config
	
	var offset_pos = init_config["offset_pos"] 		
	var init_pos = init_config["init_position"]	
	init_position = Vector3((offset_pos.x + init_pos["x"]) * SConv.NM2GDM , 
							(offset_pos.y + init_pos["y"]) * SConv.FT2GDM , 
							(offset_pos.z + init_pos["z"]) * SConv.NM2GDM )	
		
	var _init_hdg = init_config["init_hdg"]												
	init_rotation = Vector3(0, _init_hdg, 0)				
	init_hdg = _init_hdg
	hdg_input = _init_hdg
	current_hdg = init_hdg			
								
	var target_pos = Vector3(init_config["target_position"]["x"] * SConv.NM2GDM,
							 init_config["target_position"]["y"] * SConv.FT2GDM,
							 init_config["target_position"]["z"] * SConv.NM2GDM)		
	
	target_position = target_pos
	
	#10NM before target 
	strike_line_z = target_pos.z - (sign(target_pos.z) * 15 * SConv.NM2GDM )
	strike_line_xL = target_pos.x - 60 * SConv.NM2GDM
	strike_line_xR = target_pos.x + 60 * SConv.NM2GDM
	
	shoot_range_variation 	= init_config['rnd_shot_dist_var']
	crank_variation 		= init_config['rnd_crank_var']
	break_variation		 	= init_config['rnd_break_var']
	
	#Prepare WEZ models	
	var input_data = ["blue_alt","diffAlt" ,"cosAspect" ,"sinAspect" ,"cosAngleOff", "sinAngleOff"]
		
	var wezModels = load_json_file(init_config['wez_models'])	
	
	rMax_calc = Expression.new()
	rMax_calc.parse(wezModels["RMAX_MODEL"], input_data)	
		
	rNez_calc = Expression.new()
	rNez_calc.parse(wezModels["RNEZ_MODEL"], input_data)	
	
	set_behavior(init_config["base_behavior"])
	share_tracks = init_config["share_tracks"] == 1
	share_states = init_config["share_states"] == 1
	
	dShotList  = init_config["beh_config"]["dShot"]
	lCrankList = init_config["beh_config"]["lCrank"]
	lBreakList = init_config["beh_config"]["lBreak"]
	
	if typeof(dShotList) != TYPE_ARRAY:
		dShotList = [dShotList]
	if typeof(lCrankList) != TYPE_ARRAY:
		lCrankList = [lCrankList]
	if typeof(lBreakList) != TYPE_ARRAY:
		lBreakList = [lBreakList]
			
	dShot  = dShotList[0]
	lCrank = lCrankList[0]
	lBreak = lBreakList[0]
	
	mission = init_config["mission"]		
	
	ownRewards = RewardsControl.new(rewConfig,self)	
	
	if team_id == 0:
		trail_color 		= Color(0.0, 0.0, 0.7, 1.0) # Blue color with 50% alpha
		trail_color_start	= Color(0.0, 0.0, 0.7, 0.0) # Starting color
		trail_color_end 	= Color(0.0, 0.0, 0.7, 1.0) # Ending color (transparent)
	else:
		trail_color 		= Color(0.7, 0.0, 0.0, 0.5) # Red color with 50% alpha
		trail_color_start	= Color(0.7, 0.0, 0.0, 0.0) # Starting color
		trail_color_end 	= Color(0.7, 0.0, 0.0, 1.0) # Ending color (transparent)

	
	update_trail_obj()
	
	var target_marker = Marker.instantiate()	
	var material = target_marker.get_active_material(0)
	var new_material = material.duplicate()  # Duplicate to avoid changing the original material used elsewhere.
	new_material.albedo_color = trail_color						
	target_marker.set_surface_override_material(0, new_material)
		
	trail_points = []			
	
	manager.get_parent().add_child(target_marker)										
	target_marker.global_position = target_pos


func set_behavior(_behavior):	
	
	if  _behavior == "baseline1" or _behavior == "baseline2" or _behavior == "duck" or\
		_behavior == "wez_eval_shooter" or _behavior == "wez_eval_target_max" or _behavior == "wez_eval_target_nez"or\
		_behavior == "external":	
		behavior = _behavior
	else:
		print("FIGTHER::WARNING:: unknow Behavior ", _behavior, "using baseline1 enemy" )
		behavior = "baseline1"	

func reset():
	
	#if init_config != null:						
	#	update_init_config(init_config)
			
	needs_reset = false
	test_executed = false
	
	var root_node = $RenderModel  # Adjust the path to your model's root node.		
	change_mesh_instance_colors(root_node, team_color)
		
	var local_offset = Vector3(0.0,0.0,0.0)
	
	if behavior == "duck" or behavior == "baseline1" or behavior == "baseline2":
				
		var rnd_offset = Vector3(init_config['rnd_offset_range']['x'],
								 init_config['rnd_offset_range']['y'],
								 init_config['rnd_offset_range']['z'])
		
		var x_offset = randf_range(-rnd_offset.x * SConv.NM2GDM, rnd_offset.x * SConv.NM2GDM)
		var z_offset = randf_range(-rnd_offset.z * SConv.NM2GDM, rnd_offset.z * SConv.NM2GDM)
		var y_offset = randf_range(-rnd_offset.y * SConv.FT2GDM, rnd_offset.y * SConv.FT2GDM)		
		local_offset = Vector3(x_offset,y_offset, z_offset)
		
		if behavior == "baseline1" or behavior == "baseline2":
			
			var agent_idx = randi_range(0, len(dShotList) - 1)
			dShot  = dShotList[agent_idx]
			lCrank = lCrankList[agent_idx]
			lBreak = lBreakList[agent_idx]
		
	position = init_position + 	local_offset
	
	if position.y < min_level:
		position.y = min_level
	elif position.y > max_level:
		position.y = max_level
	
	hdg_input 		= -init_rotation.y
	last_hdg_input 	= hdg_input	
	current_hdg 	= hdg_input
	current_level 	= position.y
	level_input 	= current_level
	current_pitch 	= 0.0
	current_time    = 0.0
	
	current_speed = max_speed * altitude_speed_factor(current_level)		
	velocity = -transform.basis.z.normalized()* current_speed

	rotation_degrees = init_rotation#Vector3(0, 0, 0) # Adjust as necessary			
	dist2go = Calc.distance2D_to_pos(global_transform.origin, target_position)			
	
	n_steps = 0
	done = false
	
	missiles = 6	
		
	AP_mode = "FlyHdg" #"GoTo" / "Hold"
		
	ownRewards.reset()
	
	activated = true
	killed = false

	tatic_status = "Search" #"MissileSupport / Commit / Evade / Recommit
	tatic_time = 0.0	
	
	
	shoot_range_error 	= -1
	crank_error 		= -1
	break_error		 	= -1
		
	HPT = null
	HRT = null
			
	data_link_list = {}
	in_flight_missile = null
	
	radar_track_list = []	
	
	trail_points = []
	
	
	
func update_scene(_tree):
				
	tree = _tree		
	var track_view_list
	if is_in_group(simGroups.ENEMY):
		track_view_list = manager.agents
	elif is_in_group(simGroups.AGENT):
		track_view_list = manager.enemies
	else:
		print("FIGTHER::WARNING::COMPONENT IN UNKNOW GROUP ", get_groups())								
	
	radar_track_list = []
	for comp in track_view_list:		
		var new_track = Track.new(comp.id, self, comp)					
		radar_track_list.append(new_track)
								
	allied_track_list = []
	for agent in tree.get_nodes_in_group(team_color_group):
		if agent.id != id:
			var new_track = Track.new(agent.id, self, agent)
			allied_track_list.append(new_track)
	
	len_allieds_data_obs = 1 if len(alliesList) >= 1 else 0
	len_tracks_data_obs = 2 if len(tree.get_nodes_in_group(simGroups.ENEMY)) > 1 else 1
								
func set_fullView(_def):
	if _def == 1:
		fullView = true
	else:
		fullView = false

func set_actions_2d(_def):
	if _def == 1:
		actions_2d = true
	else:
		actions_2d = false

func get_done():
	return done
	
func set_done_false():
	done = false
	

func get_obs(with_labels = false):
	
	var own_info = [ #9
		["own_x_pos", global_transform.origin.x / 3000.0],
		["own_z_pos", global_transform.origin.z / 3000.0],
		["own_altitude", global_transform.origin.y / 150.0],
		["own_dist_target", dist2go / 3000.0],
		["own_aspect_angle_target", Calc.get_2d_aspect_angle(current_hdg, Calc.get_hdg_2d(global_transform.origin, target_position)) / 180.0],
		["own_current_hdg", current_hdg / 180.0],
		["own_current_speed", current_speed / max_speed],
		["own_missiles", missiles / 6.0],
		["own_in_flight_missile", 1 if is_instance_valid(in_flight_missile) else 0]		
	]

	var allied_tracks_info = []

	for track in allied_track_list:
		if track.is_alive and share_tracks:
			allied_tracks_info.append_array([
				["allied_track_alt_diff_" + str(track.id), (global_transform.origin.y - track.obj.global_transform.origin.y) / 150.0],
				["allied_track_aspect_angle_" + str(track.id), track.aspect_angle / 180.0],
				["allied_track_angle_off_" + str(track.id), track.angle_off / 180.0],
				["allied_track_dist_" + str(track.id), track.dist / 3000.0],
				["allied_track_dist2go_" + str(track.id), track.obj.dist2go / 3000.0],
				["allied_track_detected_" + str(track.id), 1]
			])
		else:
			allied_tracks_info.append_array([
				["allied_track_alt_diff_" + str(track.id), 0.0],
				["allied_track_aspect_angle_" + str(track.id), Calc.get_2d_aspect_angle(current_hdg, 0.0) / 180.0],
				["allied_track_angle_off_" + str(track.id), 0.0],
				["allied_track_dist_" + str(track.id), -1.0],
				["allied_track_dist2go_" + str(track.id), 0.5],
				["allied_track_detected_" + str(track.id), 0]
			])
	
	var tracks_info = []	
	
	var track_info_null = [ #13
			["track_alt_diff", 0.0],
			["track_aspect_angle", Calc.get_2d_aspect_angle(current_hdg, 0.0) / 180.0],
			["track_angle_off", 0.0],
			["track_dist", -1.0],
			["track_dist2go", 0.5],
			["track_own_missile_RMax", 0.0],
			["track_own_missile_Nez", 0.0],
			["track_enemy_missile_RMax", 0.0],
			["track_enemy_missile_Nez", 0.0],
			["track_threat_factor", 0.0],
			["track_offensive_factor", 0.0],
			["track_is_missile_support", 0.0],
			["track_detected", 0]
		]
	
	for track in radar_track_list:		
		if track.is_alive:			
							
			tracks_info.append_array([
				["track_alt_diff_" + str(track.id), (global_transform.origin.y - track.obj.global_transform.origin.y) / 150.0],
				["track_aspect_angle_" + str(track.id), track.aspect_angle / 180.0],
				["track_angle_off_" + str(track.id), track.angle_off / 180.0],
				["track_dist_" + str(track.id), track.dist / 3000.0],
				["track_dist2go_" + str(track.id), track.obj.dist2go / 3000.0],
				["track_own_missile_RMax_" + str(track.id), track.own_missile_RMax / 926.0],
				["track_own_missile_Nez_" + str(track.id), track.own_missile_Nez / 926.0],
				["track_enemy_missile_RMax_" + str(track.id), track.enemy_missile_RMax / 926.0],
				["track_enemy_missile_Nez_" + str(track.id), track.enemy_missile_Nez / 926.0],
				["track_threat_factor_" + str(track.id), track.threat_factor - 1],
				["track_offensive_factor_" + str(track.id), track.offensive_factor - 1],
				["track_is_missile_support_" + str(track.id), track.is_missile_support],
				["track_detected_" + str(track.id), 1 if track.detected else 0]
			])
		else:
			tracks_info.append_array([ #13
			["track_alt_diff_" + str(track.id), 0.0],
			["track_aspect_angle_" + str(track.id), Calc.get_2d_aspect_angle(current_hdg, 0.0) / 180.0],
			["track_angle_off_" + str(track.id), 0.0],
			["track_dist_" + str(track.id), -1.0],
			["track_dist2go_" + str(track.id), 0.5],
			["track_own_missile_RMax_" + str(track.id), 0.0],
			["track_own_missile_Nez_" + str(track.id), 0.0],
			["track_enemy_missile_RMax_" + str(track.id), 0.0],
			["track_enemy_missile_Nez_" + str(track.id), 0.0],
			["track_threat_factor_" + str(track.id), 0.0],
			["track_offensive_factor_" + str(track.id), 0.0],
			["track_is_missile_support_" + str(track.id), 0.0],
			["track_detected_" + str(track.id), 0]
		])
			
			
	
	var obs = own_info + tracks_info + allied_tracks_info
	
	var obs_values = obs.map(func(item): return item[1])
	
	if with_labels:
		var obs_labels = obs.map(func(item): return item[0])    	
		return {"obs": obs_values, "labels": obs_labels}
	else:		
		return {"obs": obs_values}
	

func get_reward():		
	return ownRewards.get_step_rewards()
	
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
	
	if action_type == "Low_Level_Continuous":
	
		if actions_2d:
			return {				
				"input" : {
					"size": 3,
					"action_type": "continuous"
				} 
			}
		else:
			return {				
				"input" : {
					"size": 4,
					"action_type": "continuous"
				} 
			}
									
	elif action_type == "Low_Level_Discrete":         		
		
		if actions_2d:
			return {									
						"fire_input" : {
						"size": 1,
						"action_type": "discrete"
					},
						"turn_input" : {
						"size": 5,
						"action_type": "discrete"
					}
			}
		else:
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
		level_input = (last_level_input * 25000.0 + 25000.0) * SConv.FT2GDM  	
		desiredG_input = (last_desiredG_input * (max_g  - 1.0) + (max_g + 1.0))/2.0	
		shoot_input = 0 if last_fire_input <= 0 else 1
	
	elif action_type == "Low_Level_Discrete":  
								
		hdg_input = Calc.get_desired_heading(current_hdg, turn_conv[action["turn_input"]])		
		if not actions_2d:
			level_input = level_conv[action["level_input"] ]					
		desiredG_input = g_conv[action["turn_input"]] 
		shoot_input = action["fire_input"]    
		
		last_hdg_input 		= action["turn_input"] / action_turn_len
		last_desiredG_input = g_conv[action["turn_input"]] / action_turn_len
		if not actions_2d:
			last_level_input= action["level_input"] / action_level_len
		last_fire_input 	= action["fire_input"] 


func get_current_inputs():
	return [hdg_input, level_input, desiredG_input, shoot_input]

	
func process_tracks():	

	var max_treat = 0.0
	var max_offensive = 0.0
	var new_HPT = null
	var new_HRT = null
					
	for track in radar_track_list:						
								
		if track.obj.activated:
			
			track.update_track(self, track.obj, current_time)
			
			track.dl_track = false
			
			if track.just_detected:			
				track.just_detected = false				
				
				if track.is_missile_support:
					if is_instance_valid(in_flight_missile):			
						if not in_flight_missile.pitbull and in_flight_missile != null:
							in_flight_missile.recover_support() 
						HPT = track
				
			if track.just_lost:
				ownRewards.add_detect_loss_rew()				
				track.just_lost = false				
								
				if track.is_missile_support:					
					if is_instance_valid(in_flight_missile):			
						if not in_flight_missile.pitbull and in_flight_missile != null:
							in_flight_missile.lost_support() 
							ownRewards.add_detect_loss_rew(5.0)
			
			track.is_alive = manager.last_team_dl_tracks[team_id].get(track.id, false) or track.is_alive
						
			if track.is_alive:				
								
				if track.detected or manager.last_team_dl_tracks[team_id].get(track.id, false):
					
					if track.detected:
						manager.team_dl_tracks[team_id][track.id] = true 
					
					track.update_wez_data(get_wez_for_track(track))						
					
					if track.threat_factor > max_offensive: # and track.obj.get_meta('id') == 1:
						max_offensive = track.offensive_factor					
						new_HPT = track
					
					ownRewards.add_keep_track_rew()
										
					if track.threat_factor > max_treat: # and track.obj.get_meta('id') == 1:
						max_treat = track.threat_factor					
						new_HRT = track
											
					track.dl_track = not track.detected	
				#else:
				#	print("ERROROROROR")																						
			
										
		else:
			track.is_alive = false
			track.detected = false
			manager.team_dl_tracks[team_id][track.id] = false
												
	if HPT != null:			
		if not HPT.is_missile_support or not HPT.is_alive:
			HPT = new_HPT
	else:
		HPT = new_HPT
			
	HRT = new_HRT	
		
func process_behavior(delta_s):
			
	tatic_time += delta_s		
	
	if behavior == "duck":			
		
		hdg_input = Calc.clamp_hdg(Calc.get_hdg_2d(global_transform.origin, target_position ))			
		#hdg_input = current_hdg + 45#Calc.clamp_hdg(Calc.get_hdg_2d(global_transform.origin, target_position ))			
		#desiredG_input = 5
		#level_input = 45000
		
		return
		
	elif behavior == "test" or behavior == "wez_eval_target_max":		
		return
			
	elif behavior == "wez_eval_target_nez":		
								
		if manager.agents[0].in_flight_missile and not test_executed:			
			hdg_input = Calc.clamp_hdg(Calc.get_hdg_2d(global_transform.origin, manager.enemies[0].global_transform.origin) + 180.0)
			#hdg_input = Calc.clamp_hdg(current_hdg + 180 )#fmod(oposite_hdg + 180.0, 360.0) - 180.0
			desiredG_input = 6.0
			test_executed = true
		return
	
	elif behavior == "wez_eval_shooter" :
		if not test_executed:
			launch_missile_at_target(radar_track_list[0])	
			test_executed = true
			return
					
	elif behavior == "baseline1" or behavior == "baseline2":
				
		#Define new shot distance with randominess
		if shoot_range_error == -1:		
			shoot_range_error =  1 + randf_range(-shoot_range_variation , shoot_range_variation)								
		if break_error == -1:		
			break_error =  1 + randf_range(-break_variation , break_variation)						
		if crank_error == -1:		
			crank_error =  1 + randf_range(-crank_variation , crank_variation)						
				
		
		#print(id, " : " ,tatic_status, tatic_time, HPT)
		if tatic_status != "Evade" and HPT != null and\
		   HPT.detected and HPT.threat_factor > (lBreak * break_error + 0.5 * int(HPT.is_missile_support)):
			tatic_time = 0.0					
			tatic_status = "Evade" 
			break_error = -1       						
			hdg_input = Calc.clamp_hdg(HPT.radial + 180.0)
			desiredG_input = 6.0		

		elif tatic_status == "Search" or tatic_status == "Return":
			
			if HPT != null:												
				#print(team_id, "ErrS:", shoot_range_error, " ErrB:", break_error, " ErrC:", crank_error)				
				tatic_status = "Engage"
				defense_side = 1 - randi_range(0,1) * 2 #Choose defence side        
				AP_mode = "FlyHdg"				
				desiredG_input = 3.0
				tatic_time = 0.0
				
			elif tatic_status == "Search":				
																
				if mission == "striker":
					if (sign(strike_line_z) > 0 and global_transform.origin.z > strike_line_z) or\
				   		(sign(strike_line_z) < 0 and global_transform.origin.z < strike_line_z) or\
						global_transform.origin.x > strike_line_xR or global_transform.origin.x < strike_line_xL:					
						desiredG_input = 5.0	
						tatic_status = "Strike"							
						tatic_time = 0.0					
					
				#hdg_input = -90
				if tatic_time >= 180.0:
					hdg_input = Calc.get_hdg_2d(global_transform.origin, target_position )
					
				
			elif tatic_status == "Return" and tatic_time >= 80.0:			
				hdg_input = Calc.get_hdg_2d(global_transform.origin, target_position )
				desiredG_input = 3.0	
				tatic_status = "Search"							
				tatic_time = 0.0
			
		elif tatic_status == "Strike":									
			
			if HPT != null and HPT.detected  and HPT.is_alive and HPT.offensive_factor > dShot:
				tatic_time = 0.0					
				tatic_status = "Search" 
				#print([HPT.detected,HPT.offensive_factor,HPT.radial, HPT.is_alive, HPT.id  ])       													
				hdg_input = Calc.clamp_hdg(HPT.radial)
				desiredG_input = 3.0		
			
			else:
				hdg_input = Calc.get_hdg_2d(global_transform.origin, target_position )
						
		elif tatic_status == "Engage":
			
			if HPT != null:											
																				
				do_crank 	= HPT.threat_factor > lCrank * crank_error									
				hdg_input 	= Calc.clamp_hdg(HPT.radial + 50 * int(do_crank) * defense_side)
				
				if behavior == "baseline2":
					if HPT.last_know_pos.y > level_input:
						level_input = HPT.last_know_pos.y
																										
				if HPT.offensive_factor > dShot * shoot_range_error:					
					#print( id, "(" ,current_time, " ) :", [HPT.offensive_factor, HPT.threat_factor,abs(HPT.aspect_angle)])					
					if abs(HPT.aspect_angle) < 15.0 and !HPT.is_missile_support:					
						if launch_missile_at_target(HPT):							
							tatic_status = "MissileSupport"			
							tatic_time = 0.0							
							shoot_range_error = -1							
							HPT.is_missile_support = true
							#print(tatic_status, tatic_time)
																
				if HPT.detected and HPT.threat_factor > (lBreak * break_error + 0.5 * int(HPT.is_missile_support)):
					tatic_time = 0.0					
					tatic_status = "Evade" 
					crank_error = -1
					break_error = -1       										
					hdg_input = Calc.clamp_hdg(HPT.radial + 180)#fmod(oposite_hdg + 180.0, 360.0) - 180.0
					desiredG_input = 6.0		
				
				
				if mission == "striker":
					if (sign(strike_line_z) > 0 and global_transform.origin.z > strike_line_z) or\
				   		(sign(strike_line_z) < 0 and global_transform.origin.z < strike_line_z) or\
						global_transform.origin.x > strike_line_xR or global_transform.origin.x < strike_line_xL:					
						desiredG_input = 5.0	
						tatic_status = "Strike"
						crank_error = -1							
						tatic_time = 0.0	
					
				if not HPT.is_alive:
					tatic_status = "Search"					
					hdg_input = Calc.get_hdg_2d(global_transform.origin, target_position )
					desiredG_input = 3.0
					crank_error = -1							
					tatic_time = 0.0	
							
			else:										
				tatic_status = "Evade"        
				AP_mode = "FlyHdg"				
				tatic_time = 0.0		
													
				hdg_input = Calc.clamp_hdg(current_hdg + 180)
				desiredG_input = 6.0								
				#print("ID:", get_meta("id"), ":" ,tatic_status, tatic_time, " / ", hdg_input)				
			
		elif tatic_status == "MissileSupport": 
			
			if is_instance_valid(in_flight_missile):			
				
				if in_flight_missile.pitbull or in_flight_missile == null:
				
					tatic_status = "Evade"        						
					tatic_time = 0.0		
														
					if HPT != null:
						hdg_input = Calc.clamp_hdg(HPT.radial + 180)						
					else:
						hdg_input = Calc.clamp_hdg(current_hdg + 180 - defense_side * 50.0)#fmod(oposite_hdg + 180.0, 360.0) - 180.0							
					
					desiredG_input = 6.0													
				else:
					if HPT != null:
						hdg_input = Calc.clamp_hdg(HPT.radial + defense_side * 50.0) 										
			else:								
				tatic_status = "Evade"        
				AP_mode = "FlyHdg"				
				tatic_time = 0.0		
													
				hdg_input = Calc.clamp_hdg(current_hdg + 180- defense_side * 50.0)#fmod(oposite_hdg + 180.0, 360.0) - 180.0
				desiredG_input = max_g			
				#print(tatic_status, tatic_time)
				
		elif tatic_status == "Evade" and tatic_time >= 80.0:
			
			tatic_status = "Search"					
			hdg_input = Calc.get_hdg_2d(global_transform.origin, target_position )
			desiredG_input = 3.0							
			tatic_time = 0.0		
			
	else:
		print("FIGHTER::ERROR:: Unknow behavior selected ", behavior)		
		
		
func reacquired_track(track_id):
	
	print("reacaufpioaudspf")
	var track = radar_track_list[track_id]
	track.update_track(self, track.obj, get_wez_for_track(track))
	track.detected_status(true)
	
	if is_instance_valid(in_flight_missile):			
		if not in_flight_missile.pitbull and in_flight_missile != null:
			in_flight_missile.recover_support()			

func get_wez_for_track(track):
		
	#var input_data = ["blue_alt","diffAlt" ,"cosAspect" ,"sinAspect" ,"cosAngleOff", "sinAngleOff"]
			
	#print(id, "-input_data" ,[current_level,
	#	(current_level - track.obj.current_level),
	#						track.aspect_angle, 
	
	var ownData = [	current_level/152.4 * 0.3048,
					(current_level - track.obj.current_level)/152.4 * 0.3048,
					cos(track.aspect_angleR),sin(track.aspect_angleR), 
					cos(track.angle_offR),sin(track.angle_offR)]
					
	var ownRMax = rMax_calc.execute(ownData)
	if ownRMax <=0: 
		ownRMax	= 0.01
	
	var ownRNez = rNez_calc.execute(ownData)
	
	if ownRNez <= 0: 
		ownRNez	= 0.01
							
	var enemyData
	var enemyRMax
	var enemyRNez
	
	if abs(track.inv_aspect_angle) > track.obj.radar_hfov[1]:
		
		enemyData = [track.obj.current_level/152.4 * 0.3048,
								(track.obj.current_level - current_level)/152.4 * 0.3048,							
								cos(deg_to_rad(track.obj.radar_hfov[1])),sin(deg_to_rad(track.obj.radar_hfov[1])),
								-1.0, 0.0, -1.0, 0.0 ]	
		enemyRMax = rMax_calc.execute(enemyData) / (1.0 + abs(track.inv_aspect_angle)/180.0)		
		enemyRNez = rNez_calc.execute(enemyData) / (1.0 + abs(track.inv_aspect_angle)/180.0)
		
		if enemyRMax <=0: 
			enemyRMax	= 0.01
		if enemyRNez <=0: 
			enemyRNez	= 0.01
	
	
													
	else:
		enemyData = [track.obj.current_level/152.4 * 0.3048,
								(track.obj.current_level - current_level)/152.4 * 0.3048,							
								cos(track.inv_aspect_angleR),sin(track.inv_aspect_angleR),
								cos(track.inv_angle_offR),sin(track.inv_angle_offR)]		
		enemyRMax = rMax_calc.execute(enemyData)		
		enemyRNez = rNez_calc.execute(enemyData)
									
	#print([current_level/152.4/3,(current_level - track.obj.current_level)/152.4/3,cos(track.aspect_angle),sin(track.aspect_angle), cos(track.angle_off),sin(track.angle_off)])
	#print(team_id, ":", [ownRMax, ownRNez, enemyRMax, enemyRNez])
	if enemyRMax <=0: 
		enemyRMax	= 0.01
	if enemyRNez <=0: 
		enemyRNez	= 0.01
	
	return [ownRMax, ownRNez, enemyRMax, enemyRNez]

func _physics_process(delta: float) -> void:
	
	current_time += delta
	current_hdg = rad_to_deg(-global_transform.basis.get_euler().y)		
	current_level = global_transform.origin.y
	current_pitch = rad_to_deg(global_transform.basis.get_euler().x)
	
	#print(id,"| Level: ", current_level / SConv.FT2GDM, " Pitch: ", current_pitch, " HDG: ", current_hdg)
	
	if n_steps % action_repeat == 0:
		
		dist2go = Calc.distance2D_to_pos(global_transform.origin, target_position)			
		process_tracks()		
		process_allied_tracks()	
		if behavior != "external":						
			process_behavior(delta * (n_steps - last_beh_proc))
			last_beh_proc = n_steps
		
	if  behavior == "external"  and shoot_input > 0 and HPT != null:
		
		if abs(HPT.aspect_angle) < 30.0 and !HPT.is_missile_support:
			if launch_missile_at_target(HPT): 									
				shoot_input = -1		
		else:
			ownRewards.add_missile_no_fire_rew()
			
	
	var turn_g = clamp(desiredG_input, 1.0,  max_g * altitude_g_factor(current_level)) * SConv.GRAVITY_GDM
	var turn_speed =  turn_g / velocity.length() 
	
	process_manouvers_action()
	
	# Rotate the transform based checked the input values
	transform.basis = transform.basis.rotated(transform.basis.x.normalized(), pitch_input * pitch_speed * delta)
	transform.basis = transform.basis.rotated(Vector3.UP, -turn_input * turn_speed * delta)	
		
	$RenderModel.rotation.z = lerp($RenderModel.rotation.z, float(turn_input) , turn_speed)
	$RenderModel.rotation.x = lerp($RenderModel.rotation.x, -float(pitch_input), turn_speed )

	current_speed = max_speed * altitude_speed_factor(current_level)	
	
	velocity = -transform.basis.z.normalized() * current_speed	
		
	set_velocity(velocity)
	set_up_direction(Vector3.UP)
	move_and_slide()
	
	n_steps += 1
	
	# Update the trail
	if n_steps % trail_update_rate == 0:
		update_trail()
			
func process_manouvers_action():
	
	#print(_heuristic)
	if _heuristic == "model":
		return	
	#if _heuristic == "human":
		#turn_input = Input.get_action_strength("roll_left") - Input.get_action_strength("roll_right")
		#pitch_input = Input.get_action_strength("pitch_up") - Input.get_action_strength("pitch_down")
	#
	if _heuristic == "AP":						
		#if AP_mode == "GoTo": 													#
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
			var adjusted_turn_input = hdg_diff / 60.0  
			turn_input = clamp(adjusted_turn_input, -1.0, 1.0)
#			
		# -------- Level Adjust ---------- #
		#			
			#Limit Level Inputs
			if level_input <= min_level:
				level_input = min_level
			elif level_input >= max_level:
				level_input = max_level
				
			var level_diff = level_input - current_level			
			var adjusted_pitch_input = level_diff 			  
			
			var desired_pitch = clamp(adjusted_pitch_input, min_pitch, max_pitch)																	
			var pitch_diff = desired_pitch - current_pitch						
			pitch_input = deg_to_rad(pitch_diff)
			
			#if level_diff < 3.0:				
			#	print(current_time)
			#	print(id, " LevelDiff: ", level_diff, " PitchInput: ", pitch_input, " Desired:", desired_pitch, " Curr:", current_pitch )				

#func exited_game_area():
	#done = true
	#reward -= 10.0
	#exited_arena = true
	#reset()
									

func launch_missile_at_target(target_track):
		
	if missiles > 0 and target_track.detected:
		
		#There are already a missile in flight this missile lost support
		if is_instance_valid(in_flight_missile):			
			if not in_flight_missile.pitbull and in_flight_missile != null:
				in_flight_missile.lost_support()
				in_flight_missile.missile_track.is_missile_support = false																
				
		var new_missile = missile.instantiate()
		#change_mesh_instance_colors(new_missile, team_color)		
		manager.add_child(new_missile)										
		new_missile.add_to_group(simGroups.MISSILE)
		new_missile.global_position = global_position
		
		new_missile.launch(self, target_track)
		target_track.is_missile_support = true			
		
		in_flight_missile = new_missile		
								
		missiles -= 1		
		ownRewards.add_missile_fire_rew()
		manager.inform_state(team_id, "missile")
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
		manager.inform_state(team_id, "killed") 		
					
func reactivate():
	# Enabling processing
	set_process(true)
	set_physics_process(true)	
	collision_layer = init_layer
	collision_mask = init_mask
	input_ray_pickable = true	
	visible = true
	activated = true
	killed = false
	done = false
	ownRewards.reset()
	missiles = 6	
	
func inform_missile_miss(_missile):
	ownRewards.add_missile_miss_rew()					
	_missile.missile_track.is_missile_support = false					
	if in_flight_missile == _missile:
		in_flight_missile = null
							

	
	
func update_scale(_factor):
	var current_scale =get_node("RenderModel").get_scale()
	get_node("RenderModel").set_scale(current_scale * _factor)

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

func load_json_file(file_path):
	var file = FileAccess.open(file_path, FileAccess.READ)

	if file:
		var json_string = file.get_as_text()
		file.close()

		var json = JSON.new()
		var parse_result = json.parse(json_string)

		if parse_result == OK:
			var data = json.get_data()
			return data
		else:
			print("JSON Parse Error: ", json.get_error_message())
			return null
	else:
		print("File not found: ", file_path)
		return null

func update_trail():
	trail_points.append(global_transform.origin)
	if trail_points.size() > max_trail_points:
		trail_points.pop_front()

	draw_trail()

func draw_trail():
	if trail_points.size() < 3:
		return

	# Clear previous surfaces
	trail_mesh.clear_surfaces()
	trail_mesh.surface_begin(Mesh.PRIMITIVE_LINE_STRIP)

	for i in range(trail_points.size()):
		var point = trail_points[i]
		var t = float(i) / float(trail_points.size() - 1)
		var color = trail_color_start.lerp(trail_color_end, t)
		trail_mesh.surface_set_color(color)
		trail_mesh.surface_add_vertex(point)

	trail_mesh.surface_end()
	

func process_allied_tracks():
	for track in allied_track_list:
		
		if track.obj.activated:
			track.update_allied_track(self, track.obj, current_time)
		else:
			track.is_alive = false
	
func update_trail_obj():
	
	
	# Create the ImmediateMesh and the material once
	trail_mesh = ImmediateMesh.new()
		
	trail_material = StandardMaterial3D.new()			
	trail_mesh.surface_set_material(0, trail_material)
	trail_node.mesh = trail_mesh
	
	var override_material = trail_material.duplicate()
	override_material.albedo_color = trail_color
	override_material.flags_unshaded = true
	override_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	override_material.flags_transparent = true
	override_material.vertex_color_use_as_albedo = true
	trail_node.material_override = override_material
