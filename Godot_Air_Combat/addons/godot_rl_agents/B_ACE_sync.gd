extends Node
# --fixed-fps 2000 --disable-render-loop

const MAJOR_VERSION := "0"
const MINOR_VERSION := "1" 
const DEFAULT_PORT := "11008"

@onready var mainView = get_tree().root.get_node("B_ACE")
@onready var mainViewPort = get_tree().root.get_node("B_ACE/Simulations")
@onready var mainCanvas = get_tree().root.get_node("B_ACE/CanvasLayer")
@onready var fps_show = mainView.get_node("CanvasLayer/Control/FPS_Show")
@onready var phy_show = mainView.get_node("CanvasLayer/Control/PHY_Show")
@onready var steps_show = mainView.get_node("CanvasLayer/Control/Steps_Show")

const SimManager = preload("res://SimManager.tscn")

var envConfig

var simConfig
#Default line params GodotRL Config
var action_repeat
var renderize 
var sim_speed = 1.0
var phy_fps
var speed_up 
var seed

#Aditional Env Config
var parallel_envs 

#Experiment Mode 
var experiment_mode
var experiment_runs_per_case
var experiment_current_run
var experiment_results
var experiment_in_progress = false

var simulation_list 

var n_action_steps : int = 0
var physics_updates = 0
var last_check = 0.0

var rng = RandomNumberGenerator.new()

var stream : StreamPeerTCP = null
var connected = false
var message_center
var should_connect = true

var need_to_send_obs = false
var args = null
@onready var start_time = Time.get_ticks_msec()
var initialized = false
var just_reset = false
var stop_simulation = false

# Called when the node enters the scene tree for the first time.
func _ready():
		
	await get_tree().root.ready
	get_tree().set_pause(true) 
	_initialize()
	
	await get_tree().create_timer(1.0).timeout
	get_tree().set_pause(false) 
	
	physics_updates = 0
	last_check = Time.get_ticks_msec()
	
func _handshake():
	#print("performing handshake")
	
	var json_dict = _get_dict_json_message()
	assert(json_dict["type"] == "handshake")
	var major_version = json_dict["major_version"]
	var minor_version = json_dict["minor_version"]
	if major_version != MAJOR_VERSION:
		print("WARNING: major verison mismatch ", major_version, " ", MAJOR_VERSION)  
	if minor_version != MINOR_VERSION:
		print("WARNING: minor verison mismatch ", minor_version, " ", MINOR_VERSION)
		
	#env.debug_text.add_text("\nConnection Success") 	

func _get_dict_json_message():
	# returns a dictionary from of the most recent message
	# this is not waiting	
	while stream.get_available_bytes() == 0:
		stream.poll()
		if stream.get_status() != 2:
			print("server disconnected status, closing")
			get_tree().quit()
			return null

		OS.delay_usec(10)
		
	var message = stream.get_string()
	var json_data = JSON.parse_string(message)
	
	return json_data

func _send_dict_as_json_message(dict):
	stream.put_string(JSON.stringify(dict))

func _send_env_info():
	var json_dict = _get_dict_json_message()
	assert(json_dict["type"] == "env_info")
		
	var observation_labels = {}
	for agent in simulation_list[0].agents:
		observation_labels[agent.id] = agent.get_obs(true)["labels"]
	
	var message = {
		"type" : "env_info",		
		"observation_space" : simulation_list[0].agents[0].get_obs_space(),
		"observation_labels": observation_labels,
		"action_space": simulation_list[0].agents[0].get_action_space(),
		"n_agents": len(simulation_list[0].agents)
		}		
	_send_dict_as_json_message(message)

func connect_to_server():
	#print("Waiting for one second to allow server to start")
	OS.delay_msec(1000)
	#print("trying to connect to server")
	stream = StreamPeerTCP.new()
		
	var ip = "127.0.0.1"
	var port = _get_port()
	var connect = stream.connect_to_host(ip, port)
	#stream.set_no_delay(true) # TODO check if this improves performance or not
	stream.poll()
	return stream.get_status() == 2

func _get_args():
	
	var arguments = {}
	for argument in OS.get_cmdline_args():
		#print(argument)
		if argument.find("=") > -1:
			var key_value = argument.split("=")
			arguments[key_value[0].lstrip("--")] = key_value[1]
		else:
			# Options without an argument will be present in the dictionary,
			# with the value set to an empty string.
			arguments[argument.lstrip("--")] = ""

	return arguments   

func _set_view_features():	
	mainCanvas.btn_speed_up.set_text(str(speed_up) + "X")	
		
func _get_port():    
	return args.get("port", DEFAULT_PORT).to_int()
		
func _create_simulations(_agents_config_dict, _experiment_cases=null):
	
	for container in mainViewPort.get_children():
		container.queue_free()	
	simulation_list = []
	
	var main_view_size = mainViewPort.get_rect().size
	var cols = min(parallel_envs, 5)
	var rows = ceil(float(parallel_envs) / cols)
	var sim_width = main_view_size.x / cols
	var sim_height = main_view_size.y / rows
	
	# Define a small border size (in pixels)
	var border_size = 1.0
	
	# Calculate the normalized border size as a fraction of the viewport size
	var border_x = border_size / main_view_size.x
	var border_y = border_size / main_view_size.y
	
	var x = 0
	var y = 0
	
	for i in range(parallel_envs):
				
		var case_config = _agents_config_dict.duplicate()
		
		if _experiment_cases != null:
			assert(len(_experiment_cases) == parallel_envs)
			case_config = _agents_config_dict.duplicate()
			update_dict(case_config, _experiment_cases[i]["AgentsConfig"])			
			
						
		var viewport_container = SimManager.instantiate()
		var viewport = viewport_container.get_node("SubViewport")
		var new_simulation = viewport.get_node("SimManager")		
		# Set the size of the viewport
		viewport.size = Vector2(sim_width, sim_height)		
		
		# Enable "Own World" on the viewport
		viewport.world_3d = World3D.new()

		# Set the render target of the viewport
		viewport.render_target_update_mode = SubViewport.UPDATE_WHEN_VISIBLE
		viewport.render_target_clear_mode = SubViewport.CLEAR_MODE_ALWAYS
		
		
		# Set the position of the ViewportContainer with a border
		viewport_container.anchor_left = float(x) / cols + (border_x * x)
		viewport_container.anchor_right = viewport_container.anchor_left + 1.0 / cols - 2 * border_x
		viewport_container.anchor_top = float(y) / rows + (border_y * y)
		viewport_container.anchor_bottom = viewport_container.anchor_top + 1.0 / rows - 2 * border_y

		mainViewPort.add_child(viewport_container)
		
		var _tree = get_tree()
		new_simulation.tree = _tree	
		
		new_simulation.initialize(i, _tree, envConfig, case_config)
		viewport.uavs = new_simulation.fighters

		simulation_list.append(new_simulation)

		x += 1
		if x >= cols:
			x = 0
			y += 1

							
func _initialize_simulation(new_simulation, i, _tree, envConfig, case_config):
	new_simulation.initialize(i, _tree, envConfig, case_config)

func disconnect_from_server():
	stream.disconnect_from_host()

func _initialize():		
			
	args = _get_args()			
	
	#Load Default Configs
	simConfig = load_json_file('res://assets/Default_Sim_Config.json')	
	#Update the Default config with the received args
	update_dict(simConfig['EnvConfig'], args)
	envConfig = simConfig['EnvConfig']		
		
	seed = envConfig["seed"]
	seed(seed)
	
	phy_fps 		= envConfig["phy_fps"]
	speed_up 		= envConfig["speed_up"]
	renderize 		= envConfig["renderize"]
	action_repeat 	= int(envConfig["action_repeat"])
	parallel_envs 	= envConfig["parallel_envs"]  #Will receive default at this point	
	experiment_mode	= envConfig["experiment_mode"]#Will receive default at this point		
		
	Engine.physics_ticks_per_second = speed_up * phy_fps  
	Engine.time_scale = speed_up * 1.0 		
	RenderingServer.render_loop_enabled = (renderize == 1)		
			
	connected = connect_to_server()
	if connected:
		_handshake()
		#print("HandShake Done")		
		_wait_for_configuration()		
		if not experiment_mode:
			_send_env_info()
	else:		
		_create_simulations(simConfig['AgentsConfig'])
		initialized = true
		for sim in simulation_list:
			sim._reset_simulation()

		
	_set_view_features()	

func _physics_process(delta): 
		
	physics_updates += 1.0    
	if Time.get_ticks_msec() - last_check >= 100:
		
		#phy_show.text = str(1 / Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS))		
		sim_speed = physics_updates / phy_fps * 10.0
		phy_show.text = str(sim_speed)
		fps_show.text = str(Performance.get_monitor(Performance.TIME_FPS))
		
		if renderize:
			if  sim_speed * 4 > 30:
				Engine.max_fps = sim_speed * 4 #physics_updates / phy_fps * 10.0
			else:
				Engine.max_fps = 30
				
		physics_updates = 0.0
		last_check = Time.get_ticks_msec()
		
	if n_action_steps % action_repeat != 0 and not stop_simulation:
		n_action_steps += 1						
		return
	
	steps_show.text = str(n_action_steps/action_repeat )
	#Reach This part only every ActionRepeat Steps
	n_action_steps += 1			
	
	if connected:		
		#RL Mode
		if not experiment_mode:
			get_tree().set_pause(true) 
			
			if just_reset:		
				#for sim in simulation_list:																		
				#	print(sim._collect_results()," - ", phy_show.text, "X" )				
				just_reset = false
				var obs = _get_obs_from_simulations()				
				
				var obs_dict = {}
				var i = 0
				for agent in simulation_list[0].agents:
					obs_dict[agent.agent_name] = obs[i]
					i = i + 1					
			
				var reply = {
					"type": "reset",
					"obs": obs
				}
				_send_dict_as_json_message(reply)
				# this should go straight to getting the action and setting it checked the agent, no need to perform one phyics tick
				get_tree().set_pause(false) 
				return
			
			if need_to_send_obs:
				need_to_send_obs = false
				var reward = _get_reward_from_simulations()
				var done = _get_dones_from_simulations_agents()				
				var obs = _get_obs_from_simulations()
				
				var obs_dict  	= {}
				var done_dict 	= {}
				var reward_dict = {}
				
				var i = 0
				for agent in simulation_list[0].agents:
					obs_dict[agent.agent_name] = obs[i]
					done_dict[agent.agent_name] = done[i]
					reward_dict[agent.agent_name] = reward[i]
					i = i + 1

									
				var reply = {
					"type": "step",
					"obs": obs_dict,
					"reward": reward_dict,
					"done": done_dict					
				}
				_send_dict_as_json_message(reply)
								
			var handled = handle_message()
		
		#Experiment MODE 
		elif experiment_in_progress:			
						
			_get_reward_from_simulations()
									
			if _check_all_sims_done():
				experiment_current_run += 1
				
				var result = _collect_experiment_result(experiment_current_run)
				
				experiment_results.append(result)

				if experiment_current_run >= experiment_runs_per_case:
					var reply = {
						"type": "experiment_results",
						"results": experiment_results
					}
					_send_dict_as_json_message(reply)
					
					experiment_in_progress = false
													
					_wait_for_configuration()
				else:
					var reply = {
						"type": "experiment_step",
						"run_finished": str(experiment_current_run) 
					}
					_send_dict_as_json_message(reply)
					
					_reset_all_sims()
														
	#Not Connected
	else:					
		#Test Actions
		if false:
			var actions = [{"turn_input" : 0, "fire_input" :  0, "level_input" : 2}]#,	
		
		_check_all_sims_done()
		_get_reward_from_simulations()
		var obs = _get_obs_from_simulations()
			
		_reset_agents_if_done()	
		
func handle_message() -> bool:
	# get json message: reset, step, close
	var message = _get_dict_json_message()
	
	if message["type"] == "close":
		print("received close message, closing game")
		for sim in simulation_list:
			sim.queue_free()
		simulation_list.clear()
		get_tree().quit()
		get_tree().set_pause(false)
		return true
		
	if message["type"] == "reset":		
								
		if len(simulation_list) == 1:			
			var results = simulation_list[0]._collect_results()			
			mainCanvas.update_results(results)
			mainCanvas.update_scores(results[1]['killed'], results[0]['killed'])
			simulation_list[0]._reset_simulation()	
			
			#var reply = {
			#	"type": "final_results",			
			#	"result": results
			#}				#        
			#_send_dict_as_json_message(reply) 		
		else:
			var index = 0
			for sim in simulation_list:
				simulation_list[index]._reset_simulation()
				index += 1
		
		just_reset = true	
		n_action_steps = 0			
		
		get_tree().set_pause(false) 
		
		#print("resetting forcing draw")
#        RenderingServer.force_draw()
#        var obs = _get_obs_from_agents()
#        print("obs ", obs)
		
		
		return true
		
	if message["type"] == "call":
		var method = message["method"]
		
		var results = ""
		if method == "last":
			results = simulation_list[0]._collect_last_results()	
			#var returns = _call_method_on_agents(method)			
		else:
			results = simulation_list[0]._collect_last_results()	
				
		var reply = {
			"type": "call",
			"returns": results
		} 
			
		#print("calling method from Python")
		_send_dict_as_json_message(reply)		
		get_tree().set_pause(false)   
		
		return true
	
	if message["type"] == "action":
		
		var actions = message["action"]						
		var index = 0
		if len(simulation_list) == 1:
			simulation_list[0]._set_agent_actions(actions)
		else:
			for action in actions:
				simulation_list[index]._set_agent_actions(action)
				index += 1
						
		need_to_send_obs = true
		get_tree().set_pause(false) 
			
		return true
		
	if message["type"] == "experiment_config":
		var config = message["config"]
		for sim in simulation_list:
			sim.handle_experiment_config(config)
		get_tree().set_pause(false) 
		return true
		
	print("message was not handled")
	return false

func _check_all_sims_done():
		
	for sim in simulation_list:
		if not sim.ready_to_reset:
			return false
	return true

func _reset_agents_if_done():
				
	var index = 0
	var finalStatus = []
	for sim in simulation_list:
		
		if sim.ready_to_reset:								
			n_action_steps = 0
			finalStatus.append(sim._collect_results())			
			var results = sim._collect_results()			
			#if sim == simulation_list[0]:
			mainCanvas.update_results(results)			
			mainCanvas.update_scores(results[1]['killed'], results[0]['killed'])
			sim._reset_simulation()
			
			
		else:
			finalStatus.append(null)
	
	return finalStatus		
					
func _input(event):	
	
	if Input.is_action_just_pressed("r_key"):
		just_reset = true
		n_action_steps = 0			
		_reset_all_sims()
	
func clamp_array(arr : Array, min:float, max:float):
	var output : Array = []
	for a in arr:
		output.append(clamp(a, min, max))
	return output	

func _reset_all_sims():	
	for sim in simulation_list:		
		sim._reset_simulation()
		
func _reset_all_sim(sim_index):	
	simulation_list[sim_index]._reset_simulation()
	
		
func _get_obs_from_simulations():
		
	if len(simulation_list) == 1:		
		return simulation_list[0]._get_obs_from_agents()
	
	else:
		var envs_obs = []
		for sim in simulation_list:
			var sim_obs = sim._get_obs_from_agents()		
			envs_obs.append(sim_obs)		
		return envs_obs


func _get_reward_from_simulations():
	
	if len(simulation_list) == 1:
		return simulation_list[0]._get_reward_from_agents()
	else:
		var envs_rews = []
		for sim in simulation_list:
			var sim_rew = sim._get_reward_from_agents()
			envs_rews.append(sim_rew)
		return envs_rews
	
func _get_dones_from_simulations_agents():
	
	if len(simulation_list) == 1:
		return simulation_list[0]._get_done_from_agents()
	else:
		var agents_dones = []
		for sim in simulation_list:
			var sim_dones = sim._get_done_from_agents()
			sim_dones.append(sim_dones)
		return agents_dones
	
func _get_dones_from_simulations_enemies():
	
	if len(simulation_list) == 1:
		return simulation_list[0]._get_done_from_enemies()
	else:
		var enemies_dones = []
		for sim in simulation_list:
			var sim_dones = sim._get_done_from_enemies()
			sim_dones.append(sim_dones)
		return enemies_dones
	
func _wait_for_configuration():	

	var config_message = _get_dict_json_message()	
	if config_message["type"] != "config":
		if config_message["type"] != "close":					
			print("Wrong message received, expected type 'config' or  'close' received ", config_message["type"])
		get_tree().quit()
		get_tree().set_pause(false) 
		return true		
		
	
	var env_config_msg 	= config_message['env_config']
	update_dict(envConfig,env_config_msg)
			
	parallel_envs 	= int(envConfig.parallel_envs)	
	experiment_mode	= int(envConfig.experiment_mode)
	
	var agents_config_msg 	= config_message['agents_config']	
	var agents_config = simConfig["AgentsConfig"].duplicate(true)	
	
	update_dict(agents_config, agents_config_msg)
		
		
	if experiment_mode == 1:
			
		var experiment_config = config_message['experiment_config']
		_run_experiment(agents_config, experiment_config)
	
	else:
		_create_simulations(agents_config)
		initialized = true
		for sim in simulation_list:
			sim._reset_simulation()
	
func _run_experiment(agents_config_msg, experiment_config):
	
	#print("Running experiment with configuration:", experiment_config)
	
	experiment_runs_per_case = experiment_config.get("runs_per_case", 10)
	envConfig["parallel_envs"] = len(experiment_config['cases'])
	parallel_envs 	= envConfig["parallel_envs"]
	
	
	# Create simulations based on the experiment configuration
	_create_simulations(agents_config_msg, experiment_config.get("cases", null))
	
	initialized = true
	experiment_in_progress = true
	experiment_results = []
	experiment_current_run = 0

	_reset_all_sims()
	
func _collect_experiment_result(run_num):
	var _results = []
	for simulation in simulation_list: 
		
		var final_results = simulation._collect_results()
		
		var sim = simulation
		final_results[0]["beh"] = [sim.fighters[0].dShot, sim.fighters[0].lCrank, sim.fighters[0].lBreak]
		final_results[1]["beh"] = [sim.fighters[1].dShot, sim.fighters[1].lCrank, sim.fighters[1].lBreak]
		mainCanvas.update_results(final_results)		
		mainCanvas.update_scores(final_results[1]['killed'], final_results[0]['killed'])
		
		var sim_result = {
			"env_id" : simulation.id,
			"run_num": run_num,
			"final_results" : final_results		
		}
							
		_results.append(sim_result)
		
	return _results
		

func are_all_true(array):
	
	for value in array:
		if not value:
			return false
	return true

func update_dict(org_dict: Dictionary, new_config: Dictionary):
	# Iterate over the keys in the new_config dictionary	
	for key in new_config:  		
		if org_dict.has(key): 
			if typeof(new_config[key]) == TYPE_DICTIONARY:
				update_nested_dict(org_dict[key], new_config[key])
			# Otherwise, update the value directly
			else:				
				org_dict[key] = new_config[key]

func update_nested_dict(existing_dict: Dictionary, new_dict: Dictionary):   
	for key in new_dict:        
		if existing_dict.has(key):            
			if typeof(new_dict[key]) == TYPE_DICTIONARY:
				update_nested_dict(existing_dict[key], new_dict[key])            
			else:
				existing_dict[key] = new_dict[key]
				
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
