extends Node


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
	var detected

	func _init(_id, _obj, _dist, _radial, _detected):
		self.id = _id
		self.obj = _obj
		self.dist = _dist
		self.radial = _radial
		self.detected = _detected
	
	func update_dist_radial(_dist, _radial):
		self.dist = _dist
		self.radial = _radial
	
	func detected_status(_detected):
		self.detected = _detected
		
class RewardsControl:
	
	var mission = 0.0
	var missile_fire = 0.0
	var missile_miss = 0.0
	var detect_loss = 0.0
	var hit_enemy = 0.0
	var hit_own = 0.0
	var final_reward = 0.0
	
	var mission_factor
	var missile_fire_factor
	var missile_miss_factor
	var detect_loss_factor
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
			 	_missile_fire_factor = 0.2,
				_missile_miss_factor = -0.5,
				_detect_loss_factor = -0.1,
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
		missile_miss_factor = _missile_miss_factor
		detect_loss_factor = _detect_loss_factor
		hit_enemy_factor = _hit_enemy_factor
		hit_own_factor = _hit_own_factor
		situation_factor = _situation_factor 
		
		final_team_killed_factor = _final_team_killed_factor
		final_enemy_on_target_factor = _final_enemy_on_target_factor
		final_enemies_killed_factor = _final_enemies_killed_factor
		final_max_cycles_factor = _final_max_cycles_factor
	
	func add_mission_rew(ref_value):
		mission += mission_factor * ref_value
		#print("Figther::" , Owner.get_meta("id" ), "::Info::Mission Rewards -> ", mission_factor * ref_value )
	
	func add_missile_fire_rew():
		missile_fire += missile_fire_factor
		#print("Figther::Info::missile_fire Rewards -> ", missile_fire )
	
	func add_missile_miss_rew():
		missile_miss += missile_miss_factor
		#print("Figther::Info::missile_miss Rewards -> ", missile_miss )
	
	func add_detect_loss_rew():
		detect_loss += detect_loss_factor
		#print("Figther::", Owner.get_meta("id" ), "::Info::hit_enemy Rewards -> ", hit_enemy )
		
	func add_hit_enemy_rew():
		hit_enemy += hit_enemy_factor
	
	func add_hit_own_rew():
		hit_own += hit_own_factor
		#print("Figther::" , Owner.get_meta("id"), "::Info::hit_own Rewards -> ", hit_own )
		
	func get_total_rewards_and_reset():
		var total_rewards = mission + missile_fire + missile_miss + \
							detect_loss + hit_enemy + hit_own + final_reward
		#print("Figther::Info::Total Rewards -> ", total_rewards )
		# Reset the values
		mission = 0.0
		missile_fire = 0.0
		missile_miss = 0.0
		detect_loss = 0.0
		hit_enemy = 0.0
		hit_own = 0.0
		final_reward = 0.0
		return total_rewards
	
	func add_final_episode_reward(condition):
						
		if condition == "Enemy_Achieved_Target":
			final_reward += final_enemy_on_target_factor			
		elif condition == "Enemies_Killed":
			final_reward += final_enemies_killed_factor  + final_max_cycles_factor
			#print("Figther::Info::Enemies_Killed Rewards -> ", final_enemies_killed_factor )			
		elif condition == "Team_Killed":
			final_reward += final_team_killed_factor + final_enemy_on_target_factor
			#print("Figther::Info::TEAM_Killed Rewards -> ", final_team_killed_factor )			
		elif condition == "Max_Cycles":
			final_reward += final_max_cycles_factor
			#print("Figther::Info::Rewards Added Max_Cycles -> ", final_max_cycles_factor )
		else:
			print("Figther::Warning Trying to add unknow final reward (", condition , ")")			


