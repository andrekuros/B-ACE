extends Node
# --fixed-fps 2000 --disable-render-loop

const MAJOR_VERSION := "0"
const MINOR_VERSION := "3" 
const DEFAULT_PORT := "11008"

const DEFAULT_NUM_SIMS := 1
const DEFAULT_DEBUG := 0

const DEFAULT_SEED := "1"
const DEFAULT_PHYSICS_FPS := "20"
const DEFAULT_ACTION_REPEAT := "20" 

@export var num_sims = 1
@export var speed_up = 2000
@export var renderize = 1
@export var debug = false

@onready var mainView = get_tree().root.get_node("B_ACE")
@onready var mainViewPort = get_tree().root.get_node("B_ACE/Simulations")
@onready var mainCanvas = get_tree().root.get_node("B_ACE/CanvasLayer")

var experimentWez =  {  "runs_per_eval"  :  10,
						"sum_results"  :  0,
						"eval_dist" : [20, 30, 40],
						"runs_step" : 0
					}
var runExperiment = null#experimentWez

@onready var fps_show = mainView.get_node("CanvasLayer/Control/FPS_Show")
@onready var debug_window = mainView.get_node("DebugWindow")

const simManager = preload("res://SimManager.tscn")

var simulation_list 

var action_repeat = 20
var phy_fps = 20

var n_action_steps = 0
var physics_updates = 0
var elapsed_time = 0.0

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
	elapsed_time = 0.0
	
	if not debug:
		debug_window.visible = false
		

func _handshake():
	print("performing handshake")
	
	var json_dict = _get_dict_json_message()
	assert(json_dict["type"] == "handshake")
	var major_version = json_dict["major_version"]
	var minor_version = json_dict["minor_version"]
	if major_version != MAJOR_VERSION:
		print("WARNING: major verison mismatch ", major_version, " ", MAJOR_VERSION)  
	if minor_version != MINOR_VERSION:
		print("WARNING: minor verison mismatch ", minor_version, " ", MINOR_VERSION)
		
	#env.debug_text.add_text("\nConnection Success") 
	print("handshake complete")

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
	
	var message = {
		"type" : "env_info",
		#"obs_size": agents[0].get_obs_size(),
		"observation_space": simulation_list[0].agents[0].get_obs_space(),
		"action_space": simulation_list[0].agents[0].get_action_space(),
		"n_agents": len(simulation_list[0].agents)
		}
	#env.debug_text.add_text(message) 
	_send_dict_as_json_message(message)

func connect_to_server():
	print("Waiting for one second to allow server to start")
	OS.delay_msec(1000)
	print("trying to connect to server")
	stream = StreamPeerTCP.new()
	
	# "localhost" was not working on windows VM, had to use the IP
	var ip = "127.0.0.1"
	var port = _get_port()
	var connect = stream.connect_to_host(ip, port)
	stream.set_no_delay(true) # TODO check if this improves performance or not
	stream.poll()
	return stream.get_status() == 2

func _get_args():
	#print("getting command line arguments")
#	
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

func _get_speedup():
	#print("SpeedUp: " , args, " Val: ", str(speed_up))
	mainCanvas.btn_speed_up.set_text(str(speed_up) + "X")
	return args.get("speedup", str(speed_up)).to_int()

func _get_renderize():	
	#print("Renderize: " , args, " Val: ", str(renderize))
	return args.get("renderize", str(renderize)).to_int() == 1
	
func _get_port():    
	return args.get("port", DEFAULT_PORT).to_int()

func _set_seed():
	seed(args.get("env_seed", DEFAULT_SEED).to_int())
		
func _create_simulations(args):
	simulation_list = []

	var main_view_size = mainViewPort.get_rect().size
	var cols = min(num_sims, 5)
	var rows = ceil(float(num_sims) / cols)
	var sim_width = main_view_size.x / cols
	var sim_height = main_view_size.y / rows

	var x = 0
	var y = 0

	for i in range(num_sims):
		var viewport_container = simManager.instantiate()
		var viewport = viewport_container.get_node("SubViewport")
		var new_simulation = viewport.get_node("SimManager")

		# Set the size of the viewport
		viewport.size = Vector2(sim_width, sim_height)
		
		# Enable "Own World" on the viewport
		viewport.world_3d = World3D.new()

		# Set the render target of the viewport
		viewport.render_target_update_mode = SubViewport.UPDATE_WHEN_VISIBLE
		viewport.render_target_clear_mode = SubViewport.CLEAR_MODE_ALWAYS

		# Set the position of the ViewportContainer
		viewport_container.anchor_left = float(x) / cols
		viewport_container.anchor_right = viewport_container.anchor_left + 1.0 / cols
		viewport_container.anchor_top = float(y) / rows
		viewport_container.anchor_bottom = viewport_container.anchor_top + 1.0 / rows

		mainViewPort.add_child(viewport_container)

		var _tree = get_tree()
		new_simulation.tree = _tree
		new_simulation.initialize(i, _tree, args)
		viewport.uavs = new_simulation.fighters

		simulation_list.append(new_simulation)

		x += 1
		if x >= cols:
			x = 0
			y += 1
							

func disconnect_from_server():
	stream.disconnect_from_host()

func _initialize():		
			
	args = _get_args()		
	
	action_repeat = args.get("action_repeat", DEFAULT_ACTION_REPEAT).to_int()
	
	_set_seed()		
	
	_create_simulations(args)
	
	phy_fps = args.get("physics_fps", DEFAULT_PHYSICS_FPS).to_int()
	args["phy_fps"] = phy_fps
			
	Engine.physics_ticks_per_second = _get_speedup() * phy_fps  # Replace with function body.
	Engine.time_scale = _get_speedup() * 1.0 	
	prints("physics ticks", Engine.physics_ticks_per_second, Engine.time_scale, _get_speedup(), speed_up)	
	
	RenderingServer.render_loop_enabled = _get_renderize()
	
	connected = connect_to_server()
	if connected:		
		#_set_heuristic("AP")
		_handshake()
		_send_env_info()
		
	initialized = true 	
	
	for sim in simulation_list:
		sim._reset_simulation()
	
	if debug:		
		initialize_debug()	

func _physics_process(delta): 

	
	physics_updates += 1    
	elapsed_time += delta	
			
	var current_time = Time.get_ticks_msec()	
	if current_time - elapsed_time >= 200:
		fps_show.text = str(physics_updates / 20 * 5 )
	#	print(str(physics_updates / 4))
		physics_updates = 0
		elapsed_time = current_time
	
	if n_action_steps % action_repeat != 0 and not stop_simulation:
		n_action_steps += 1						
		return
	
	#Reach This part only every ActionRepeat Steps
	n_action_steps += 1	
	
	if connected:
		get_tree().set_pause(true) 
		
		if just_reset:
			just_reset = false
			var obs = _get_obs_from_simulations()
		
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
			#_reset_agents_if_done() # this ensures the new observation is from the next env instance : NEEDS REFACTOR			
			var obs = _get_obs_from_simulations()
			
			var reply = {
				"type": "step",
				"obs": obs,
				"reward": reward,
				"done": done
			}
			_send_dict_as_json_message(reply)
		
		var handled = handle_message()
	else:						
		
		if runExperiment != null:
			
			
			var finalStatus = _reset_agents_if_done()			
			if finalStatus[0] != null:
				experimentWez["sum_results"] += finalStatus[0]
				experimentWez["runs_step"] += 1
				
			
			if experimentWez["runs_step"] == 10:
				print(experimentWez["runs_step"])
				experimentWez["runs_step"] = 0
				experimentWez["sum_results"] = 0
				
			
			
			
		
		else:#print(n_action_steps, _get_reward_from_agents())	
			if false:
				var actions = [{"turn_input" : 0, "fire_input" :  0, "level_input" : 2}]#,
				# {"turn_input": 4, "fire_input" :  0,  "level_input" : 4}] 
				for sim in simulation_list:
					sim._set_agent_actions(actions)
			#_set_agent_actions(actions)
			#print(n_action_steps, _get_reward_from_agents())		
			_reset_agents_if_done()	
		
	
	if debug:
		
		var agent_idx = debug_window.selected_agent
		
		var obs = simulation_list[0].agents[agent_idx].get_obs()
		debug_window.update_obs( obs['obs'] )
				
		var actions_values = simulation_list[0].agents[agent_idx].get_current_inputs()
		debug_window.update_actions( actions_values )		

func handle_message() -> bool:
	# get json message: reset, step, close
	var message = _get_dict_json_message()
				
	if message["type"] == "close":
		print("received close message, closing game")
		get_tree().quit()
		get_tree().set_pause(false) 
		return true
		
	if message["type"] == "reset":
		#print("resetting all agents")
		
		
		if len(simulation_list) == 1:
			simulation_list[0]._reset_simulation()
		else:
			var index = 0
			for sim in simulation_list:
				simulation_list[index]._reset_simulation()
				index += 1
		
		just_reset = true		
		get_tree().set_pause(false) 
		
		#print("resetting forcing draw")
#        RenderingServer.force_draw()
#        var obs = _get_obs_from_agents()
#        print("obs ", obs)
#        var reply = {
#            "type": "reset",
#            "obs": obs
#        }
#        _send_dict_as_json_message(reply)   
		return true
		
#	if message["type"] == "call":
#		var method = message["method"]
#		var returns = _call_method_on_agents(method)
#		var reply = {
#			"type": "call",
#			"returns": returns
#		}
		#print("calling method from Python")
#		_send_dict_as_json_message(reply)   
#		return handle_message()
	
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
		
	print("message was not handled")
	return false

#func _call_method_on_agents(method):
#	var returns = []
#	for agent in agents:
#		returns.append(agent.call(method))
#		
#	return returns

func _reset_agents_if_done():
			
	var index = 0
	var finalStatus = []
	for sim in simulation_list:
		var donesAgents  = sim._check_all_done_agents()
		var donesEnemies  = sim._check_all_done_enemies()		
		if donesAgents or donesEnemies:
		#print(_get_reward_from_agents())
			finalStatus.append(sim.finalState.blues_killed)
			sim._reset_simulation()
		else:
			finalStatus.append(null)
	return finalStatus		
					

func _input(event):	
	
	if Input.is_action_just_pressed("r_key"):
		just_reset = true		
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
	
		
func initialize_debug():
	
	var obs = simulation_list[0].fighters[0].get_obs(true)
	var actions_labels = ['hdg', 'level', 'g', 'fire']
	var actions_values = [-1, -1, -1, -1]
	
	debug_window.initialize( 	obs["labels"],
								obs["obs"],
								actions_labels,
								actions_values )
	debug_window.visible = true
	
	debug_window.selected_agent_control.create_agent_buttons(len(simulation_list[0].agents))

func are_all_true(array):
	for value in array:
		if not value:
			return false
	return true
