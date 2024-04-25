extends Node

const Calc = preload("res://Calc.gd") # Ensure you have a Calc script for calculations
									
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
	var vert_aspect_angle
	var aspect_angle
	var angle_off
	var inv_aspect_angle
	var inv_angle_off
	var vert_aspect_angleR
	var aspect_angleR
	var angle_offR
	var inv_aspect_angleR
	var inv_angle_offR
	var last_know_pos
	var last_detection
	var radar_range
	var radar_hfov
	var radar_vfov
	var last_track_hdg
	var detected
	var just_detected
	var just_lost
	var is_alive	
	var is_missile_support
	var own_missile_RMax
	var own_missile_Nez
	var enemy_missile_RMax
	var enemy_missile_Nez	
	var threat_factor
	var offensive_factor
	
	func _init(_id, fighter, track_obj):
		id = _id		
		obj = track_obj
		last_know_pos = fighter.global_transform.origin
		last_track_hdg = 0.0
		last_detection = -500.0 #dead at the beginning
		is_alive = false
		is_missile_support = false
		radar_range= fighter.radar_range
		radar_hfov = fighter.radar_hfov
		radar_vfov = fighter.radar_vfov
		
		update_track(fighter, track_obj, 0.0)
					
	
	func is_track_detectable() -> bool:
			
		if dist > radar_range:
			return false
		
		if aspect_angle < radar_hfov[0] or aspect_angle > radar_hfov[1]:
			return false
		if vert_aspect_angle < radar_vfov[0] or vert_aspect_angle > radar_vfov[1]:
			return false
		return true
	
	func update_track(fighter, track_obj, time_detected):
								
		dist 			  = fighter.global_transform.origin.distance_to(track_obj.global_transform.origin)
		radial			  = Calc.get_hdg_2d(fighter.global_transform.origin, track_obj.global_transform.origin)
		
		vert_aspect_angle 	= Calc.get_vertical_aspect_angle(fighter, track_obj)
		angle_off 		  	= Calc.get_2d_angle_off(fighter.current_hdg, track_obj.current_hdg )
		aspect_angle 	  	= Calc.get_2d_aspect_angle(fighter.current_hdg, radial)
		
		inv_angle_off 	  	= -angle_off
		inv_aspect_angle	= Calc.get_2d_aspect_angle(track_obj.current_hdg, radial - 180)
		
		#print(fighter.id, ":ASPECT: ", aspect_angle, " AOff: ", angle_off, " Rad: ", radial, " HDG: ", fighter.current_hdg)
		#print(fighter.id, ":invASPECT: ", inv_aspect_angle, " InvAOff: ", inv_angle_off)
				
		vert_aspect_angleR	= deg_to_rad(vert_aspect_angle)
		angle_offR 		  	= deg_to_rad(angle_off)
		aspect_angleR 	  	= deg_to_rad(aspect_angle)
		inv_angle_offR 	  	= deg_to_rad(inv_angle_off)
		inv_aspect_angleR	= deg_to_rad(inv_aspect_angle)
				
		var is_detectable = is_track_detectable()		
				
		if is_detectable:
			#print(" detectable:", [angle_off,
			#						aspect_angle,
			#						vert_aspect_angle])
			last_know_pos = track_obj.global_transform.origin
			last_track_hdg = track_obj.current_hdg 
			last_detection = time_detected
			is_alive = true
			if not detected:
				just_detected = true			
				detected = true
		else:			
			if time_detected - last_detection > 20.0:
				is_alive = false
			
			if detected:
				just_lost = true			
				detected = false
		
	
	func update_wez_data(wez_ranges):
		
		own_missile_RMax 	= wez_ranges[0] * SConv.NM2GDM
		own_missile_Nez		= wez_ranges[1] * SConv.NM2GDM
		enemy_missile_RMax	= wez_ranges[2] * SConv.NM2GDM
		enemy_missile_Nez	= wez_ranges[3] * SConv.NM2GDM
						
		if dist <= own_missile_RMax:
			if dist > own_missile_Nez and own_missile_Nez != own_missile_RMax:				
				offensive_factor = 1.0 - 0.5 * (dist - own_missile_Nez) / (own_missile_RMax - own_missile_Nez)
			else:			
				offensive_factor = min(own_missile_Nez / dist, 2.0)
		else:
			offensive_factor = 0.5 * exp(-2.0 * ((dist - own_missile_RMax)/own_missile_RMax))
			#threat_factor = 0.5 * own_missile_RMax / dist
					
		if dist <= enemy_missile_RMax:
			if dist > enemy_missile_Nez and enemy_missile_Nez != enemy_missile_RMax:				
				threat_factor = 1.0 - 0.5 * (dist - enemy_missile_Nez) / (enemy_missile_RMax - enemy_missile_Nez)
			else:			
				threat_factor = min(enemy_missile_Nez / dist, 2.0)
		else:
			threat_factor = 0.5 * exp(-2.0 * ((dist- enemy_missile_RMax)/enemy_missile_RMax))
			#threat_factor = 0.5 * own_missile_RMax / dist
		if offensive_factor > 2:
			print([own_missile_RMax, own_missile_Nez, enemy_missile_RMax, enemy_missile_Nez], [dist])
			print("Factors:", [offensive_factor, threat_factor])
		
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
	const DEFAULT_MISSION_FACTOR := 0.001
	const DEFAULT_MISSILE_FIRE_FACTOR := -0.1
	const DEFAULT_MISSILE_NO_FIRE_FACTOR := -0.001
	const DEFAULT_MISSILE_MISS_FACTOR := -0.5
	const DEFAULT_DETECT_LOSS_FACTOR := -0.1
	const DEFAULT_KEEP_TRACK_FACTOR := 0.001
	const DEFAULT_HIT_ENEMY_FACTOR := 3.0
	const DEFAULT_HIT_OWN_FACTOR := -5.0	
	const DEFAULT_MISSION_ACCOMPLISHED_FACTOR := 10.0
	
	var printRewards = false
	var cumulated_rewards = 0.0
	var mission = 0.0
	var	missile_fire = 0.0
	var	missile_miss = 0.0
	var	detect_loss = 0.0
	var	keep_track = 0.0
	var	hit_enemy = 0.0
	var	hit_own = 0.0		
	var	final_reward = 0.0
	var mission_factor: float
	var missile_fire_factor: float
	var missile_no_fire_factor: float
	var missile_miss_factor: float
	var detect_loss_factor: float
	var keep_track_factor: float
	var hit_enemy_factor: float
	var hit_own_factor: float	
	var mission_accomplished_factor: float
	var Owner_obj = null
	var max_cycles = 36000.0 / 20.0

	func _init(config, _owner_obj):
						
		#print(config, _owner_obj.id)
		self.mission_factor = config.get("mission_factor", DEFAULT_MISSION_FACTOR)
		self.missile_fire_factor = config.get("missile_fire_factor", DEFAULT_MISSILE_FIRE_FACTOR)
		self.missile_no_fire_factor = config.get("missile_no_fire_factor", DEFAULT_MISSILE_NO_FIRE_FACTOR)
		self.missile_miss_factor = config.get("missile_miss_factor", DEFAULT_MISSILE_MISS_FACTOR)
		self.detect_loss_factor = config.get("detect_loss_factor", DEFAULT_DETECT_LOSS_FACTOR)
		self.keep_track_factor = config.get("keep_track_factor", DEFAULT_KEEP_TRACK_FACTOR)
		self.hit_enemy_factor = config.get("hit_enemy_factor", DEFAULT_HIT_ENEMY_FACTOR)
		self.hit_own_factor = config.get("hit_own_factor", DEFAULT_HIT_OWN_FACTOR)
		self.mission_accomplished_factor = config.get("mission_accomplished_factor", DEFAULT_MISSION_ACCOMPLISHED_FACTOR)		
		
		self.Owner_obj = _owner_obj		
		max_cycles = _owner_obj.max_cycles
	
	func add_mission_rew(ref_value):
		mission += mission_factor * ref_value 
		
	func add_missile_fire_rew():
		missile_fire += missile_fire_factor
		
	func add_missile_no_fire_rew():
		missile_fire += missile_no_fire_factor
		
	func add_missile_miss_rew():
		missile_miss += missile_miss_factor
		
	func add_detect_loss_rew(multiplier = 1.0):
		detect_loss += detect_loss_factor * multiplier
		
	func add_keep_track_rew():
		keep_track += keep_track_factor
					
	func add_hit_enemy_rew():		
		hit_enemy += hit_enemy_factor				
	
	func add_hit_own_rew():
		hit_own += hit_own_factor
				
	func get_step_rewards():
		var step_rewards = mission + missile_fire + missile_miss + keep_track +\
							detect_loss + hit_enemy + hit_own + final_reward
		
		#print( [mission, missile_fire, missile_miss, keep_track,\
		#					detect_loss, hit_enemy, hit_own, final_reward])
		
		cumulated_rewards += step_rewards
				
		# Reset the values
		mission = 0.0
		missile_fire = 0.0
		missile_miss = 0.0
		detect_loss = 0.0
		keep_track = 0.0
		hit_enemy = 0.0
		hit_own = 0.0		
		final_reward = 0.0
				
		return step_rewards
	
	func reset():
				
		cumulated_rewards = 0.0
		mission = 0.0
		missile_fire = 0.0
		missile_miss = 0.0
		detect_loss = 0.0
		keep_track = 0.0
		hit_enemy = 0.0
		hit_own = 0.0		
		final_reward = 0.0
		
	func get_cumulated_rewards():
		return cumulated_rewards
		
	
	func add_final_episode_reward(condition, missing_cycles, missiles_remaining = 0):
						
		if condition == "Enemy_Achieved_Target":
			final_reward -= mission_accomplished_factor
			#print("Figther::Info::Enemies_On Target Rewards -> ", final_reward )			
		elif condition == "Enemies_Killed":
			final_reward += mission_accomplished_factor
			final_reward += (keep_track_factor + mission_factor) * missing_cycles
			
		elif condition == "Team_Killed":
			final_reward -= mission_accomplished_factor
			final_reward += (missile_miss_factor * missiles_remaining)
			#print("Figther::Info::TEAM_Killed Rewards -> ", final_reward )			
		
		elif condition == "Max_Cycles":
			final_reward += mission_accomplished_factor
			#print("Figther::Info::Rewards Added Max_Cycles -> ", final_reward )
		else:
			print("Figther::Warning Trying to add unknow final reward (", condition , ")")			

	

