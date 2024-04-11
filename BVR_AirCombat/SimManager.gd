extends Node3D

var fighterObj   = preload("res://Fighter.tscn")
const SConv      = preload("res://Sim_assets.gd").SConv
const SimGroups  = preload("res://Sim_assets.gd").SimGroups

@onready var mainView = get_tree().root.get_node("B_ACE")
var tree = null

#const RewardsControl = preload("res://Sim_assets.gd").RewardsControl

var finalState 

var id

var envConfig
var agentsConfig
var rewardsConfig
var simGroups

var agents = []
var enemies = []
var fighters = []
var agents_alive_control
var enemies_alive_control

var n_action_steps
var action_repeat
var max_cycles
var phy_fps
var physics_updates = 0
var elapsed_time = 0.0

var stop_simulation = false
var initialized = false
	
func initialize(_id, _tree, _envConfig, _agentsConfig):
		
	id = _id
	tree = _tree	
	
	envConfig = _envConfig
	
	action_repeat	= int(envConfig["action_repeat"])
	max_cycles		= int(envConfig["max_cycles"])
	
	agentsConfig = _agentsConfig.duplicate(true)
	
	simGroups = SimGroups.new(id)
	
	_set_agents(_tree)	 		
	_set_heuristic("AP")
	
	initialized = true

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _physics_process(delta):
	# Increment the physics update count
	physics_updates += 1    
	elapsed_time += delta	
				
	if agents_alive_control == 0 and not stop_simulation :		
		
		var missiles = tree.get_nodes_in_group(simGroups.MISSILE)
		if len(missiles) == 0:
			stop_simulation = true
			for agent in agents:			
				agent.ownRewards.add_final_episode_reward("Team_Killed")				
			#print("Sync::INFO::TeamKilled" )
			for enemy in enemies:
				enemy.done = true
	
	if enemies_alive_control == 0 and not stop_simulation:		
		
		var missiles = tree.get_nodes_in_group(simGroups.MISSILE)		
		if len(missiles) == 0:
			stop_simulation = true
			for agent in agents:
				agent.done = true
				agent.ownRewards.add_final_episode_reward("Enemies_Killed")					
			#print("Sync::INFO::EnemyKilled" )
				
	if n_action_steps % action_repeat != 0 and not stop_simulation:
		n_action_steps += 1	
		return
			
	#Reach This part only every ActionRepeat Steps
	n_action_steps += 1
		
	if n_action_steps >= max_cycles:
		for enemy in enemies:
			enemy.done = true 
			
		for agent in agents:
			agent.done = true 
			agent.ownRewards.add_final_episode_reward("Max_Cycles")
		
		
	#PROCCESS Global Rewards
	#Enmies Rewards are actually penaulties due to the proximity to the 
	#Enemies targets and also finish the episode in case the target is achieved	
	var enemy_goal_reward = 0.0
	var enemy_on_target = false
	
	#Calculate Penaulties for enemy distance to target	
	for enemy in enemies:		
		if enemy.activated and not enemy.get_done():										
			enemy_goal_reward += -1.0 / enemy.dist2go			
			if enemy.dist2go < 3.0: #300 meters
				enemy_on_target = true
				finalState[1]['mission'] += 1 

	if enemy_on_target:
		for agent in agents:
			agent.done = true
			agent.ownRewards.add_final_episode_reward("Enemy_Achieved_Target")
		for enemy in enemies:
			enemy.done = true
			
	#Calculate Penaulties for own distance to defense target	
	var own_goal_reward = 0.0
	for agent in agents:
		if agent.activated and not agent.get_done():							
			if agent.dist2go > 185.2 * 2 and enemies_alive_control > 0: #20NM
				own_goal_reward -= agent.dist2go / 185200
							
			#print([enemy_goal_reward, own_goal_reward, enemies_alive_control])
			#Add the calculated rews
			agent.ownRewards.add_mission_rew(enemy_goal_reward)
			agent.ownRewards.add_mission_rew(own_goal_reward)

func _set_agents(_tree):	
				
	#Scale Vectors only for Visualization	
	const visual_scaleVector = Vector3(4.0,  4.0,  4.0)
	
	var listComponents = []	
	for i in range(agentsConfig["blue_agents"]["num_agents"]):
		listComponents.append("Allied_Agent")
	
	for i in range(agentsConfig["red_agents"]["num_agents"]):
		listComponents.append("Enemy_Agent")
		
	for comp in listComponents:
		
		var newFigther = null				
		
		newFigther = fighterObj.instantiate()		
		add_child(newFigther)
		
		newFigther.manager = self
		newFigther.get_node("RenderModel").set_scale(visual_scaleVector)
		
		newFigther.phy_fps 		 = int(envConfig["phy_fps"])
		newFigther.action_repeat = int(envConfig["action_repeat"])
		newFigther.action_type 	 = envConfig["action_type"]
		
		newFigther.add_to_group(simGroups.FIGHTER)
		newFigther.simGroups = simGroups		
		newFigther.set_fullView(envConfig["full_observation"])			
		
				
		if comp == "Allied_Agent":
			
			var blue_config = agentsConfig["blue_agents"].duplicate(true)
			newFigther.team_id 	= 0
			agents.append(newFigther)			
			
			var offset_x = 0
			var num_group = _tree.get_nodes_in_group(simGroups.BLUE).size()
			if num_group % 2 == 0:
				offset_x = num_group / 2
			else:
				offset_x = -(num_group -1) / 2 - 1
			
			newFigther.add_to_group(simGroups.AGENT)							
			newFigther.add_to_group(simGroups.BLUE)
			newFigther.id = 100 +  len(agents)
			newFigther.set_meta('id', 100 +  len(agents))
			
			newFigther.team_color = "BLUE"
			newFigther.team_color_group = simGroups.BLUE
									
			blue_config["offset_pos"] = Vector3(offset_x * 6, 0.0, 0.0)			
			newFigther.update_init_config(blue_config, envConfig["RewardsConfig"])			
			newFigther.reset()
						
		else:
			var red_config = agentsConfig["red_agents"].duplicate(true)
			newFigther.team_id = 1
			enemies.append(newFigther)
									
			var num_group = _tree.get_nodes_in_group(simGroups.RED).size()
			var offset_x = 0
			if num_group % 2 == 0:
				offset_x = num_group / 2
			else:
				offset_x = -(num_group -1) / 2 - 1 
						
			newFigther.add_to_group(simGroups.ENEMY)							
			newFigther.add_to_group(simGroups.RED)
			newFigther.id = 200 +  len(agents)
			newFigther.set_meta('id', 200 +  len(enemies))
			newFigther.team_color = "RED"
			newFigther.team_color_group = simGroups.RED
			
			red_config["offset_pos"] = Vector3(offset_x * 6, 0.0, 0.0)			
			newFigther.update_init_config(red_config, envConfig["RewardsConfig"])			
			newFigther.reset()			
																										
		fighters.append(newFigther)
			
	for fighter in fighters:
		fighter.update_scene(tree)

func _reset_simulation():
	
	_reset_all_uavs()
	_reset_components()	
	
	physics_updates = 0
	elapsed_time = 0.0
	
	agents_alive_control = len(agents)
	enemies_alive_control = len(enemies)
	
	finalState = []
	
	for i in range(2):
		finalState.append( {	
				"killed" 	: 0,
				"mission"	: 0,
				"reward"  	: 0.0,
				"missile"	: 0
				})
	
	stop_simulation = false
	n_action_steps = 0

func _reset_components():	
	var missiles = tree.get_nodes_in_group(simGroups.MISSILE)
	for missile in missiles:
		missile.queue_free()
			
func _reset_all_uavs():
	
	if initialized:
		for uav in fighters:
			uav.needs_reset = true
			uav.reactivate()
			uav.reset() 
			uav.update_scene(tree) 
	
func _get_obs_from_agents():
	
	var obs = []
	for agent in agents:
		if !agent.done:
			obs.append(agent.get_obs())
		else:
			var zero_obs = []
			for i in range(len(agent.get_obs()["obs"])):
				zero_obs.append(0)
			obs.append({"obs": zero_obs})
		
	return obs
	
func _get_reward_from_agents():
	var rewards = [] 
	for agent in agents:
		rewards.append(agent.get_reward())		
		finalState[agent.team_id]["reward"] += rewards[-1]		
	return rewards    
	
func _get_done_from_agents():
	var dones = []
	for agent in agents:
		dones.append(agent.get_done())		
	return dones

func _get_done_from_enemies():
	var dones = []
	for enemy in enemies:
		dones.append(enemy.get_done())		
	return dones

func _check_all_done_agents():	
	for agent in agents:
		if not agent.get_done():
			return false					
	return true

func _check_all_done_enemies():	
	for enemy in enemies:
		if not enemy.get_done():
			return false					
	return true

func _set_agent_actions(actions):
	for i in range(len(actions)):
		#env.debug_text.add_text("\nAction:" + str(actions[i])) 
		#print(i, actions[i])
		agents[i].set_action(actions[i])
	
func _set_heuristic(heuristic):
	for agent in agents:
		agent.set_heuristic(heuristic)

func _collect_results():	
	return finalState
	
	
func inform_state(team_id, condition):	
	
	if condition == "killed":
		if team_id == 0:
			agents_alive_control  -= 1
		else:
			enemies_alive_control -= 1
				
		finalState[team_id]["killed"] 	+= 1
		
	elif condition == "missile":
		finalState[team_id]["missile"] 	+= 1		
	
