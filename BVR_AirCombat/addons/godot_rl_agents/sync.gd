extends Node
# --fixed-fps 2000 --disable-render-loop
@export var action_repeat := 8
@export var speed_up = 1
@export var renderize = 1
@export var num_uavs = 4
@export var num_targets = 10
var n_action_steps = 0


var rng = RandomNumberGenerator.new()

@onready var env = get_tree().root.get_node("FlyBy")

const SConv = preload("res://Figther_assets.gd").SConv

const MAJOR_VERSION := "0"
const MINOR_VERSION := "3" 
const DEFAULT_PORT := "11008"
const DEFAULT_SEED := "1"
const DEFAULT_ACTION_REPEAT := "8"
const DEFAULT_NUM_UAVS := "4"
const DEFAULT_NUM_TARGETS := "1"

var stream : StreamPeerTCP = null
var connected = false
var message_center
var should_connect = true
var agents
var need_to_send_obs = false
var args = null
@onready var start_time = Time.get_ticks_msec()
var initialized = false
var just_reset = false

# Called when the node enters the scene tree for the first time.

func _ready():

	#env.debug_text.add_text("\nSync Ready") 
	await get_tree().root.ready
	get_tree().set_pause(true) 
	_initialize()
	await get_tree().create_timer(1.0).timeout
	get_tree().set_pause(false) 
		
func _get_agents():
	agents = get_tree().get_nodes_in_group("AGENT")		

func _set_heuristic(heuristic):
	for agent in agents:
		agent.set_heuristic(heuristic)

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
		"observation_space": agents[0].get_obs_space(),
		"action_space":agents[0].get_action_space(),
		"n_agents": len(agents)
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
	print("getting command line arguments")
#	var arguments = {}
#	for argument in OS.get_cmdline_args():
#		# Parse valid command-line arguments into a dictionary
#		if argument.find("=") > -1:
#			var key_value = argument.split("=")
#			arguments[key_value[0].lstrip("--")] = key_value[1]
			
	var arguments = {}
	for argument in OS.get_cmdline_args():
		print(argument)
		if argument.find("=") > -1:
			var key_value = argument.split("=")
			arguments[key_value[0].lstrip("--")] = key_value[1]
		else:
			# Options without an argument will be present in the dictionary,
			# with the value set to an empty string.
			arguments[argument.lstrip("--")] = ""

	return arguments   

func _get_speedup():
	print("SpeedUp: " , args, " Val: ", str(speed_up))
	env.canvas.btn_speed_up.set_text(str(speed_up) + "X")
	return args.get("speedup", str(speed_up)).to_int()

func _get_renderize():	
	print("Renderize: " , args, " Val: ", str(renderize))
	return args.get("renderize", str(renderize)).to_int() == 1
	
func _get_port():    
	return args.get("port", DEFAULT_PORT).to_int()

func _set_seed():
	var _seed = args.get("env_seed", DEFAULT_SEED).to_int()	

func _set_num_uavs():	
	num_uavs = args.get("num_uavs", DEFAULT_NUM_UAVS).to_int()    
	const model_scaleVector  = Vector3(1.0/SConv.SCALE_FACTOR, 1.0/SConv.SCALE_FACTOR, 1.0/SConv.SCALE_FACTOR)
	const invert_scaleVector = Vector3(SConv.SCALE_FACTOR, SConv.SCALE_FACTOR, SConv.SCALE_FACTOR)	
	const visual_scaleVector = Vector3(3.0,  3.0,  3.0)
	
	for i in range(num_uavs):
		
		var addPlane = null				
		addPlane = env.fighterObj.instantiate()
		#addPlane.set_scale(model_scaleVector)	
		addPlane.get_node("RenderModel").set_scale(visual_scaleVector)	
		#addPlane.get_node("Radar").set_scale(invert_scaleVector)		
		addPlane.add_to_group("AGENT")		
		
		var team_id =  i % 2 + 0  # Assigns UAVs alternately to team 1 or 2
		
		if team_id == 1:
			addPlane.init_position = Vector3(i * 5.0 * SConv.NM2GDM, 20000 * SConv.FT2GDM , 30 * SConv.NM2GDM )
			addPlane.init_rotation = Vector3(0, 0, 0)			
		else:
			addPlane.init_position = Vector3(i * 5.0 * SConv.NM2GDM, 20000 * SConv.FT2GDM, -30 * SConv.NM2GDM )
			addPlane.init_rotation = Vector3(0, 180, 0)
		
		
		addPlane.init_hdg = addPlane.init_rotation.y
		addPlane.desired_hdg = addPlane.init_hdg
				
		addPlane.set_meta('id', i + 2)
		addPlane.team_id = team_id
		addPlane.add_to_group("blue" if addPlane.team_id == 1 else "red" )
		
		env.get_node("Fighters").add_child(addPlane)    
		env.uavs.append(addPlane)
		
		
func _set_num_targets():
	num_targets = args.get("num_targets", DEFAULT_NUM_TARGETS).to_int()
	
	for i in range(num_targets-1):
		var addGoal = (env.goals[0][0]).duplicate()		
		addGoal.position = Vector3(rng.randf_range(-350.0, 350.0),50,rng.randf_range(-350.0, -30.0))		
		addGoal.set_meta('id', i + 1)
		env.get_node("Goals").add_child(addGoal)
		env.goals.append([addGoal,-1])	
		env.goalsPending.append(len(env.goals)-1)
	
	
func _set_action_repeat():
	action_repeat = args.get("action_repeat", DEFAULT_ACTION_REPEAT).to_int()
	
func disconnect_from_server():
	stream.disconnect_from_host()

func _initialize():		
	
	args = _get_args()	
	_set_seed()	
	_set_action_repeat()
	_set_num_uavs()
	_get_agents()
	_set_num_targets()
	_set_heuristic("AP") 	
		
	Engine.physics_ticks_per_second = _get_speedup() * 20  # Replace with function body.
	Engine.time_scale = _get_speedup() * 1.0 
	prints("physics ticks", Engine.physics_ticks_per_second, Engine.time_scale, _get_speedup(), speed_up)
	env.debug_text.add_text("Initial Speed " + str(speed_up) + "X" + " - Phy " + str(Engine.physics_ticks_per_second))
	
	RenderingServer.render_loop_enabled = _get_renderize()
	
	connected = connect_to_server()
	if connected:		
		#_set_heuristic("AP")
		_handshake()
		_send_env_info()
	#else:
		#_set_heuristic("AP")  

	initialized = true  

func _physics_process(delta): 
	# two modes, human control, agent control
	# pause tree, send obs, get actions, set actions, unpause tree
	if n_action_steps % action_repeat != 0:
		n_action_steps += 1
		return

	n_action_steps += 1
	
	if connected:
		get_tree().set_pause(true) 
		
		if just_reset:
			just_reset = false
			var obs = _get_obs_from_agents()
		
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
			var reward = _get_reward_from_agents()
			var done = _get_done_from_agents()
			#_reset_agents_if_done() # this ensures the new observation is from the next env instance : NEEDS REFACTOR
			
			var obs = _get_obs_from_agents()
			
			var reply = {
				"type": "step",
				"obs": obs,
				"reward": reward,
				"done": done
			}
			_send_dict_as_json_message(reply)
		
		var handled = handle_message()
	#else:
		#_reset_agents_if_done()

func handle_message() -> bool:
	# get json message: reset, step, close
	var message = _get_dict_json_message()
				
	if message["type"] == "close":
		print("received close message, closing game")
		get_tree().quit()
		get_tree().set_pause(false) 
		return true
		
	if message["type"] == "reset":
		print("resetting all agents")
		_reset_all_agents()
		just_reset = true
		env.goalsPending.append(len(env.goals)-1)
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
		
	if message["type"] == "call":
		var method = message["method"]
		var returns = _call_method_on_agents(method)
		var reply = {
			"type": "call",
			"returns": returns
		}
		print("calling method from Python")
		_send_dict_as_json_message(reply)   
		return handle_message()
	
	if message["type"] == "action":
		var action = message["action"]
		_set_agent_actions(action)		
		need_to_send_obs = true
		get_tree().set_pause(false) 
			
		return true
		
	print("message was not handled")
	return false

func _call_method_on_agents(method):
	var returns = []
	for agent in agents:
		returns.append(agent.call(method))
		
	return returns


func _reset_agents_if_done():
	for agent in agents:
		if agent.get_done(): 
			agent.set_done_false()
		agent.reactivate()

func _reset_all_agents():
	if initialized:
		for agent in agents:
			agent.needs_reset = true
			agent.reactivate()
			agent.reset()   

func _get_obs_from_agents():
	var obs = []
	for agent in agents:
		obs.append(agent.get_obs())
	return obs
	
func _get_reward_from_agents():
	var rewards = [] 
	for agent in agents:
		rewards.append(agent.get_reward())
		agent.zero_reward()
	return rewards    
	
func _get_done_from_agents():
	var dones = []
	
	for agent in agents:
		var done = agent.get_done()
		#if done: 
		#	agent.set_done_false()
		dones.append(done)
	
	return dones    
	
func _set_agent_actions(actions):
	for i in range(len(actions)):
		agents[i].set_action(actions[i])
	
func _input(event):	
	
	if Input.is_action_just_pressed("r_key"):
		just_reset = true
		env.goalsPending.append(len(env.goals)-1)
		_reset_all_agents()
		
