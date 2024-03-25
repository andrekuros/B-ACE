extends Node

const Calc = preload("res://Calc.gd") # Ensure you have a Calc script for calculations

class SimConfig:	
	
	const DEFAULT_PHYSICS_FPS := "20"
	const DEFAULT_MAX_CYCLES := "36000" # 15 * 20 * 60 (15 MINUTES REAL TIME)
	const DEFAULT_ACTION_REPEAT := "20"
	const DEFAULT_ACTION_TYPE := "Low_Level_Discrete"	
	const DEFAULT_NUM_ALLIES := "1"
	const DEFAULT_NUM_ENEMIES := "1"
	const DEFAULT_ENEMIES_BASELINE := "baseline1"
	const DEFAULT_FULL_OBSERVATION := "0"
	const DEFAULT_ACTIONS_2D := "0"
		

	var phy_fps
	var max_cycles 		
	var action_type
	var action_repeat	
	var num_allies 
	var num_enemies
	var enemies_baseline	
	var full_observation
	var actions_2d
	
	var agents_config = { "blue_agents": 
			{                        
				"init_position": {
					"x": 0.0,
					"y": 25000.0,
					"z": 30.0
				},
				"offset_pos": {
				"x": 0.0,
				"y": 0.0,
				"z": 0.0
				},
				"init_hdg": 0.0,                        
				"target_position": {
					"x": 0.0,
					"y": 25000.0,
					"z": 30.0
				},
				"behaviour": "external",
				"full_view": 0
			},
		
			"red_agents":
			{ 
				"init_position": {
				"x": 0.0,
				"y": 25000.0,
				"z": -30.0
				},
			"offset_pos": {
				"x": 0.0,
				"y": 0.0,
				"z": 0.0
			},
			"init_hdg" : 180.0,                        
			"target_position": {
				"x": 0.0,
				"y": 25000.0,
				"z": 30.0
			},
			"behaviour": "baseline1",
			"full_view": 0                    
		}
	}
	
		
	func _init(args):				
		
		self.phy_fps = args.get("phy_fps", DEFAULT_PHYSICS_FPS).to_int()
		self.max_cycles = args.get("max_cycles", DEFAULT_MAX_CYCLES).to_int()
		
		self.action_type = args.get("action_type", DEFAULT_ACTION_TYPE)
		self.action_repeat = args.get("action_repeat", DEFAULT_ACTION_REPEAT).to_int()
		
		self.num_allies = args.get("num_allies", DEFAULT_NUM_ALLIES).to_int() 
		self.num_enemies = args.get("num_enemies", DEFAULT_NUM_ENEMIES).to_int() 
		self.enemies_baseline = args.get("enemies_baseline", DEFAULT_ENEMIES_BASELINE)
		
		self.full_observation = args.get("full_observation", DEFAULT_FULL_OBSERVATION).to_int()
		self.actions_2d = args.get("actions_2d", DEFAULT_ACTIONS_2D).to_int()
		
class SimGroups:
	
	var BLUE
	var RED
	var FIGHTER
	var AGENT
	var ENEMY
	var MISSILE
	
	func _init(sim_id):
		BLUE     = "BLUE"       + str(sim_id)
		RED      = "RED"        + str(sim_id)
		FIGHTER  = "FIGHTER_"   + str(sim_id)
		AGENT    = "AGENT_"     + str(sim_id)
		ENEMY    = "ENEMIE_"    + str(sim_id)
		MISSILE  = "MISSILE_"   + str(sim_id)

class SConv:
	const SCALE_FACTOR = 100.0
	const REAL2GD = 1.0 / SCALE_FACTOR
	#const REAL2GD = 1 / 200               #GoDot meter represent 200m in real
	const NM2M    = 1852.0 
	const NM2GDM  = 1852.0 / SCALE_FACTOR           #GDM is GoDot Meters
	const KNOT2M_S = 1.0 / 1.944
	const KNOT2GDM_S = 1.0 / (1.944 * SCALE_FACTOR)
	const GDM2NM = SCALE_FACTOR / 1852.0
	const GDM_S2KNOT = 1.944 * SCALE_FACTOR
	const M_S2KNOT = 1.944
	
	const FT2M = 0.3048 
	const FT2GDM = 0.3048 / SCALE_FACTOR
	
	const GRAVITY_GDM = 9.81 * REAL2GD
	
	func _init():
		pass

class Track:
	var id
	var obj
	var dist
	var radial
	var aspect_angle
	var angle_off
	var last_know_pos	
	var own_missile_RMax
	var own_missile_Nez
	var own_missile_6h	
	var enemy_missile_RMax
	var enemy_missile_Nez
	var enemy_missile_6h
	var detected

	func _init(_id, fighter, track_obj):
		self.id = _id		
		self.obj = track_obj
		self.last_know_pos = fighter.position
		
		update_track(fighter, track_obj)
					
	func update_track(fighter, track_obj, _detected = true):
		
		self.dist = fighter.global_transform.origin.distance_to(track_obj.global_transform.origin)
		self.radial = Calc.get_hdg_2d(fighter.position, track_obj.position)        								
		self.angle_off = Calc.get_2d_aspect_angle(fighter.current_hdg, self.radial)
		self.aspect_angle = Calc.get_2d_aspect_angle(fighter.current_hdg, self.radial)				
		self.detected = _detected		
		if _detected:
			self.last_know_pos = track_obj.position
	
	func update_track_not_detected(fighter):
		self.dist = fighter.global_transform.origin.distance_to(self.last_know_pos)
		self.radial = Calc.get_hdg_2d(fighter.position, self.last_know_pos)        								
		self.angle_off = Calc.get_2d_aspect_angle(fighter.current_hdg, self.radial)
		self.aspect_angle = Calc.get_2d_aspect_angle(fighter.current_hdg, self.radial)						
		
					
	#func update_missile_ranges():
		
	#	self.own_missile_RMax
	#	self.own_missile_Nez
	#	self.own_missile_6h	
		
	#	self.enemy_missile_RMax
	#	self.enemy_missile_Nez
	#	self.enemy_missile_6h
	
	func detected_status(_detected):
		self.detected = _detected
		
	func radial2aspect_angle(own_hdg, taget_radial):		
		return clamp_hdg(taget_radial - own_hdg)
		
	func clamp_hdg(hdg):
		if hdg > 180.0:
			return hdg - 360.0
		elif hdg < -180.0:
			return hdg + 360.0
		else:
			return hdg
		
class RewardsControl:
		
	var printRewards = false
	
	var mission = 0.0
	var missile_fire = 0.0
	var missile_miss = 0.0
	var detect_loss = 0.0
	var keep_track = 0.0
	var hit_enemy = 0.0
	var hit_own = 0.0
	var final_reward = 0.0
	
	var mission_factor
	var missile_fire_factor
	var missile_no_fire_factor
	var missile_miss_factor
	var detect_loss_factor
	var keep_track_factor
	var hit_enemy_factor
	var hit_own_factor
	var situation_factor
	
	var final_team_killed_factor
	var final_enemy_on_target_factor
	var final_enemies_killed_factor
	var final_max_cycles_factor
	
	var Owner = null
	
	
	func _init(	_owner,
				_mission_factor = 1.0,
			 	_missile_fire_factor = -0.1,
				_missile_no_fire_factor = -0.001,
				_missile_miss_factor = -0.5,
				_detect_loss_factor = -0.1,
				_keep_track = 0.001,
				_hit_enemy_factor = 3.0,
				_hit_own_factor = -5.0,
				_situation_factor = 0.1, 
				_final_team_killed_factor = -5.0,
				_final_enemy_on_target_factor = -3.0,
				_final_enemies_killed_factor = 5.0,
				_final_max_cycles_factor = 3.0):
					
		Owner = _owner
		mission_factor = _mission_factor
		missile_fire_factor = _missile_fire_factor
		missile_no_fire_factor = _missile_no_fire_factor
		missile_miss_factor = _missile_miss_factor
		detect_loss_factor = _detect_loss_factor
		keep_track_factor = _keep_track 
		hit_enemy_factor = _hit_enemy_factor
		hit_own_factor = _hit_own_factor
		situation_factor = _situation_factor 
		
		final_team_killed_factor = _final_team_killed_factor
		final_enemy_on_target_factor = _final_enemy_on_target_factor
		final_enemies_killed_factor = _final_enemies_killed_factor
		final_max_cycles_factor = _final_max_cycles_factor
	
	func add_mission_rew(ref_value):
		mission += mission_factor * ref_value
		if printRewards:
			print("Figther::" , Owner.get_meta("id" ), "::Info::Mission Rewards -> ", mission )
	
	func add_missile_fire_rew():
		missile_fire += missile_fire_factor
		if printRewards:
			print("Figther::Info::missile_fire Rewards -> ", missile_fire )
	
	func add_missile_no_fire_rew():
		missile_fire += missile_no_fire_factor
		if printRewards:			
			print("Figther::Info::missile_fire Rewards -> ", missile_fire )
	
	func add_missile_miss_rew():
		missile_miss += missile_miss_factor
		if printRewards:
			print("Figther::Info::missile_miss Rewards -> ", missile_miss )
	
	func add_detect_loss_rew():
		detect_loss += detect_loss_factor
		if printRewards:
			print("Figther::", Owner.get_meta("id" ), "::Info::detect_loss Rewards -> ", detect_loss )
	
	func add_keep_track_rew():
		keep_track += keep_track_factor
		if printRewards:
			print("Figther::", Owner.get_meta("id" ), "::Info::keep_track Rewards -> ", keep_track )
					
	func add_hit_enemy_rew():
		hit_enemy += hit_enemy_factor				
	
	func add_hit_own_rew():
		hit_own += hit_own_factor
		#print("Figther::" , Owner.get_meta("id"), "::Info::hit_own Rewards -> ", hit_own )
		
	func get_total_rewards_and_reset():
		var total_rewards = mission + missile_fire + missile_miss + \
							detect_loss + hit_enemy + hit_own + final_reward
		
		if printRewards:
			print("Figther::Info::Total Rewards -> ", total_rewards )
		# Reset the values
		mission = 0.0
		missile_fire = 0.0
		missile_miss = 0.0
		detect_loss = 0.0
		keep_track = 0
		hit_enemy = 0.0
		hit_own = 0.0		
		final_reward = 0.0
				
		return total_rewards
	
	func add_final_episode_reward(condition):
						
		if condition == "Enemy_Achieved_Target":
			final_reward += final_enemy_on_target_factor			
			#print("Figther::Info::Enemies_On Target Rewards -> ", final_reward )			
		elif condition == "Enemies_Killed":
			final_reward += final_enemies_killed_factor  + final_max_cycles_factor
			#print("Figther::Info::Enemies_Killed Rewards -> ", final_reward )			
		elif condition == "Team_Killed":
			final_reward += final_team_killed_factor + final_enemy_on_target_factor
			#print("Figther::Info::TEAM_Killed Rewards -> ", final_reward )			
		elif condition == "Max_Cycles":
			final_reward += final_reward
			#print("Figther::Info::Rewards Added Max_Cycles -> ", final_reward )
		else:
			print("Figther::Warning Trying to add unknow final reward (", condition , ")")			

class FinalState:
	var blues_killed = 0
	var reds_killed = 0
	var blue_target = 0
	var red_taget = 0
	
	func _init():
		pass
	
	func reset():
		blues_killed = 0
		reds_killed  = 0
		blue_target  = 0
		red_taget    = 0
		
	

	
	

