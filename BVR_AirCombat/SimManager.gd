extends Node3D

var fighterObj   = preload("res://Fighter.tscn")
const SConv      = preload("res://Sim_assets.gd").SConv
const SimConfig  = preload("res://Sim_assets.gd").SimConfig
const SimGroups  = preload("res://Sim_assets.gd").SimGroups


@onready var mainView = get_tree().root.get_node("B_ACE")
var tree = null

const FinalState = preload("res://Sim_assets.gd").FinalState
var finalState = FinalState.new()

const RewardsControl = preload("res://Sim_assets.gd").RewardsControl
var refRewards = RewardsControl.new(self)

var id

var agents = []
var enemies = []
var fighters = []

var agents_alive_control
var enemies_alive_control
var enemies_target
var allies_target
var simConfig
var simGroups

var n_action_steps = 0
var phy_fps = 20
var physics_updates = 0
var elapsed_time = 0.0

var stop_simulation = false
var initialized = false

	
func initialize(_id, tree, args):
		
	id = _id
	
	simConfig = SimConfig.new(args)
	simGroups = SimGroups.new(id)
	finalState.reset()
	
	_set_agents(tree)	 		
	_set_heuristic("AP")
	
	initialized = true

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _physics_process(delta):
	# Increment the physics update count
	physics_updates += 1    
	elapsed_time += delta	
			
	#var current_time = Time.get_ticks_msec()	
	#if current_time - elapsed_time >= 200:
		#fps_show.text = str(physics_updates / 4)
	#	print(str(physics_updates / 4))
	#	physics_updates = 0
	#	elapsed_time = current_time
		

	if agents_alive_control == 0:		
		stop_simulation = true
		for agent in agents:			
			agent.ownRewards.add_final_episode_reward("Team_Killed")
			agents_alive_control = -1		
		#print("Sync::INFO::TeamKilled" )
		for enemy in enemies:
			enemy.done = true
	
	if enemies_alive_control == 0:		
		stop_simulation = true
		for agent in agents:
			agent.done = true
			agent.ownRewards.add_final_episode_reward("Enemies_Killed")	
			enemies_alive_control = -1
			
	if n_action_steps % simConfig.action_repeat != 0 and not stop_simulation:
		n_action_steps += 1	
		return
			
	#Reach This part only every ActionRepeat Steps
	n_action_steps += 1
	
	if n_action_steps >= simConfig.max_cycles:
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
			var dist_to_go = Calc.distance2D_to_pos(enemy.position, enemy.target_position)
			enemy.dist2go = dist_to_go
			enemy_goal_reward += -1.0 / dist_to_go			
			if dist_to_go < 3.0: #300 meters
				enemy_on_target = true
				finalState.red_taget = 1 

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
			var dist_to_pos = Calc.distance2D_to_pos(agent.position, agent.target_position)
			agent.dist2go = dist_to_pos
			if dist_to_pos > 185.2 * 2: #20NM
				own_goal_reward -= dist_to_pos / 185200
							
			#Add the calculated rews
			agent.ownRewards.add_mission_rew(enemy_goal_reward)
			agent.ownRewards.add_mission_rew(own_goal_reward)

func _set_agents(tree):	
			
	#Scale Vectors only for Visualization
	#const model_scaleVector  = Vector3(1.0/SConv.SCALE_FACTOR, 1.0/SConv.SCALE_FACTOR, 1.0/SConv.SCALE_FACTOR)
	#const invert_scaleVector = Vector3(SConv.SCALE_FACTOR, SConv.SCALE_FACTOR, SConv.SCALE_FACTOR)	
	const visual_scaleVector = Vector3(4.0,  4.0,  4.0)
	
	var listComponents = []
	
	for i in range(simConfig.num_allies):
		listComponents.append("Allied_Agent")
	
	for i in range(simConfig.num_enemies):
		listComponents.append("Enemy_Agent")
		
	for comp in listComponents:
		
		var newFigther = null				
		
		newFigther = fighterObj.instantiate()
		#get_node("ViewPort").add_child(newFigther) 
		add_child(newFigther)
		
		newFigther.manager = self
		newFigther.get_node("RenderModel").set_scale(visual_scaleVector)		
		newFigther.phy_fps = simConfig.phy_fps
		newFigther.action_repeat = simConfig.action_repeat
		newFigther.action_type = simConfig.action_type											
		newFigther.add_to_group(simGroups.FIGHTER)
		newFigther.simGroups = simGroups
		
		newFigther.set_fullView(simConfig.full_observation)	
		newFigther.set_actions_2d(simConfig.actions_2d)	
							
		if comp == "Allied_Agent":
			
			var blue_config = simConfig.agents_config["blue_agents"].duplicate(true)
			newFigther.team_id = 0
			agents.append(newFigther)			
			
			var offset_x = 0
			var num_group = tree.get_nodes_in_group(simGroups.BLUE).size()
			if num_group % 2 == 0:
				offset_x = num_group / 2
			else:
				offset_x = -(num_group -1) / 2 - 1
			
			newFigther.add_to_group(simGroups.AGENT)							
			newFigther.add_to_group(simGroups.BLUE)
			newFigther.set_meta('id', 100 +  len(agents))
			newFigther.team_color = "BLUE"
			newFigther.team_color_group = simGroups.BLUE
									
			blue_config["offset_pos"] = Vector3(offset_x * 6, 0.0, 0.0)
			print(blue_config["offset_pos"] )
			newFigther.update_init_config(blue_config)
			
			newFigther.set_behaviour("external")			 	
			#newFigther.set_behaviour("test")			 	
		else:
			var red_config = simConfig.agents_config["red_agents"].duplicate(true)
			newFigther.team_id = 1
			enemies.append(newFigther)
									
			var num_group = tree.get_nodes_in_group(simGroups.RED).size()
			var offset_x = 0
			if num_group % 2 == 0:
				offset_x = num_group / 2
			else:
				offset_x = -(num_group -1) / 2 - 1 
			
			#offset_pos = tree.get_nodes_in_group(simGroups.RED).size()
			newFigther.add_to_group(simGroups.ENEMY)							
			newFigther.add_to_group(simGroups.RED)
			newFigther.set_meta('id', 200 +  len(enemies))
			newFigther.team_color = "RED"
			newFigther.team_color_group = simGroups.RED
			
			red_config["offset_pos"] = Vector3(offset_x * 6, 0.0, 0.0)
			newFigther.update_init_config(red_config)
			
			newFigther.set_behaviour(simConfig.enemies_baseline)		
																			
		
					
		fighters.append(newFigther)
		#env.uavs.append(newFigther)			
		#env.get_node("Fighters").add_child(newFigther)    
	
	for fighter in fighters:
		fighter.update_scene(tree)

func _reset_simulation():
		
	_reset_all_uavs()
	_reset_components()	
	
	physics_updates = 0
	elapsed_time = 0.0
	
	agents_alive_control = len(agents)
	enemies_alive_control = len(enemies)
	
	finalState.reset()
	
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

func inform_kill(team_id):
	
	if team_id == 0:
		agents_alive_control    -= 1
		finalState.blues_killed += 1		
	else:
		enemies_alive_control   -= 1
		finalState.red_killed   += 1
	
	
	
