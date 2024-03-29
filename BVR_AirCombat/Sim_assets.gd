extends Node

const Calc = preload("res://Calc.gd") # Ensure you have a Calc script for calculations

class EnvConfig:	
	
	const DEFAULT_PHYSICS_FPS := 20
	const DEFAULT_MAX_CYCLES := 36000 # 30 * 20 * 60 (30 MINUTES REAL TIME)	
	const DEFAULT_PARALLEL_ENVS := 1 
	const DEFAULT_SEED := 1
	const DEFAULT_SPEED_UP := 1000
	const DEFAULT_RENDERIZE := 1
	const DEFAULT_EXPERIMENT_MODE := 0
	const DEFAULT_DEBUG_VIEW := 0
	const DEFAULT_ACTION_REPEAT := 20
	const DEFAULT_ACTION_TYPE := "Low_Level_Discrete"		
	const DEFAULT_FULL_OBSERVATION := 0
	const DEFAULT_ACTIONS_2D := 0
	
	var phy_fps: int
	var max_cycles: int
	var seed: int
	var parallel_envs: int
	var speed_up: int
	var renderize: int 
	var debug_view: int
	var experiment_mode: int 		
	var action_type: String
	var action_repeat: int		
	var full_observation: int
	var actions_2d: int		
		
	func _init(config):				
				
		self.phy_fps 		= int(config.get("phy_fps", DEFAULT_PHYSICS_FPS))
		self.max_cycles 	= int(config.get("max_cycles", DEFAULT_MAX_CYCLES))
		self.seed 			= int(config.get("seed", DEFAULT_SEED))
		self.parallel_envs	= int(config.get("parallel_envs", DEFAULT_PARALLEL_ENVS))
		
		self.speed_up		= int(config.get("speed_up", DEFAULT_SPEED_UP))
		self.renderize		= int(config.get("renderize", DEFAULT_RENDERIZE))
		self.debug_view		= int(config.get("debug_view", DEFAULT_DEBUG_VIEW))
		self.experiment_mode= int(config.get("experiment_mode", DEFAULT_EXPERIMENT_MODE))
		
		self.action_type 	= config.get("action_type", DEFAULT_ACTION_TYPE)
		self.action_repeat 	= int(config.get("action_repeat", DEFAULT_ACTION_REPEAT))
		
		self.full_observation 	= int(config.get("full_observation", DEFAULT_FULL_OBSERVATION))
		self.actions_2d 		= int(config.get("actions_2d", DEFAULT_ACTIONS_2D))
				
	
	func update_config(config):		
		
		self.max_cycles = config.get("max_cycles", self.max_cycles)
		self.seed = config.get("seed", self.seed)
		self.parallel_envs = config.get("parallel_envs", self.parallel_envs)
		self.speed_up = config.get("speed_up", self.speed_up)
		self.renderize = config.get("renderize", self.renderize)
		self.debug_view = config.get("debug_view", self.debug_view)
		self.experiment_mode= config.get("experiment_mode", self.experiment_mode)
		self.action_type = config.get("action_type", self.action_type)
		self.action_repeat = config.get("action_repeat", self.action_repeat)
		self.full_observation = config.get("full_observation", self.full_observation)
		self.actions_2d = config.get("actions_2d", self.actions_2d)
							
class SimConfig:	
		
	const DEFAULT_NUM_ALLIES := 1
	const DEFAULT_NUM_ENEMIES := 1
	const DEFAULT_ENEMIES_BEHAVIOR:= "baseline1"
	const DEFAULT_AGENTS_BEHAVIOR :=  "baseline1"	
			
	var num_allies 
	var num_enemies
	var enemies_behavior
	var agents_behavior	
		
	var agents_config = { "blue_agents": 
			{                        
				"init_position": {"x": 0.0, "y": 25000.0,"z": 30.0},
				"offset_pos": {	"x": 0.0, "y": 0.0, "z": 0.0},
				"init_hdg": 0.0,                        
				"target_position": {"x": 0.0,"y": 25000.0,"z": -30.0},
				"rnd_offset_range":{"x": 15.0,"y": 10000.0,"z": 5.0},
				#"rnd_offset_range":{"x": 0.0,"y": 0.0,"z": 0.0},
				"rnd_shot_dist_var": 0.0 																						
			},
		
			"red_agents":
			{ 
				"init_position": {"x": 0.0,"y": 25000.0,"z": -30.0},
				"offset_pos": {"x": 0.0,"y": 0.0,"z": 0.0},
				"init_hdg" : 180.0,                        
				"target_position": {"x": 0.0,"y": 25000.0,"z": 30.0},
				"rnd_offset_range":{"x": 15.0,"y": 10000.0,"z": 5.0},
				#"rnd_offset_range":{"x": 0.0,"y": 0.0,"z": 0.0},
				"rnd_shot_dist_var": 0.0					
		}
	}
			
	func _init(config):				
						
		self.num_allies 		= config.get("num_allies", DEFAULT_NUM_ALLIES)
		self.num_enemies 		= config.get("num_enemies", DEFAULT_NUM_ENEMIES)
		self.enemies_behavior 	= config.get("enemies_behavior", DEFAULT_ENEMIES_BEHAVIOR)
		self.agents_behavior 	= config.get("agents_behavior", DEFAULT_AGENTS_BEHAVIOR)
		self.agents_config 		= config.get("agents_config" , self.agents_config)
		
		
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
		
	

	
	

