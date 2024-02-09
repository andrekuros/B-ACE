extends CharacterBody3D

# Maximum airspeed
var max_flight_speed = 50
# Turn rate
@export var turn_speed = 5.0
@export var level_speed = 12.0
@export var turn_acc = 4.0
@onready var env = get_tree().root.get_node("FlyBy")

@onready var tasksDoneViewer = env.get_node("CanvasLayer/Control/TasksDone")

# Climb/dive rate
var pitch_speed = 2.0
# Wings "autolevel" speed
# Throttle change speed
var throttle_delta = 30
# Acceleration/deceleration
var acceleration = 6.0
# Current speed
var forward_speed = 0
# Throttle input speed
var target_speed = 0

#State -> Heading
#var hdg = 0 #0 is flying X positive direction (Z == 0)

#var velocity = Vector3.ZERO
var found_goal = false
var exited_arena = false
var cur_goal = null
# ------- #
var turn_input = 0
var pitch_input = 0
var done = false
var _heuristic = "AP" #"model" / "AP"
var AP_mode = "GoTo" #"GoTo" / "Hold"
var holdStatus = 0
var best_goal_distance := 10000.0
var transform_backup = null
var n_steps = 0
const MAX_STEPS = 200000
var needs_reset = false
var reward = 0.0


func _ready():
	transform_backup = transform
	pass
	
func reset():
	needs_reset = false
	
	cur_goal = env.get_next_goal(null)
	transform_backup = transform_backup
	position.x = 0 + randf_range(-2,2)
	position.y = 50 + randf_range(-2,2)
	position.z = 0 + randf_range(-2,2)
	velocity = Vector3.ZERO
	rotation = Vector3.ZERO
	n_steps = 0
	found_goal = false
	exited_arena = false 
	done = false
	best_goal_distance = to_local(cur_goal.position).length()
	# reset position, orientation, velocity

func reset_if_done():
	if done:
		reset()
		
func get_done():
	return done
	
func set_done_false():
	done = false
	
func get_obs():
	if cur_goal == null:
		reset()
	#var goal_vector = (cur_goal.position - position).normalized() # global frame of reference
	var goal_vector = to_local(cur_goal.position)
	var goal_distance = goal_vector.length()
	goal_vector = goal_vector.normalized()
	goal_distance = clamp(goal_distance, 0.0, 50.0)
	
	var next_goal = env.get_next_goal(cur_goal)
	var next_goal_vector = to_local(next_goal.position)
	var next_goal_distance = next_goal_vector.length()
	next_goal_vector = next_goal_vector.normalized()
	next_goal_distance = clamp(next_goal_distance, 0.0, 50.0)  

	var obs = [
		goal_vector.x,
		goal_vector.y,
		goal_vector.z,
		goal_distance / 50.0 ,
		next_goal_vector.x,
		next_goal_vector.y,
		next_goal_vector.z,
		next_goal_distance / 50.0
	]
	
	return {"obs":obs}

func update_reward():
	reward -= 0.01 # step penalty
	reward += shaping_reward()

func get_reward():
	return reward
	
func shaping_reward():
	var s_reward = 0.0
	var goal_distance = to_local(cur_goal.position).length()
	if goal_distance < best_goal_distance:
		s_reward += best_goal_distance - goal_distance
		best_goal_distance = goal_distance
		
	s_reward /= 1.0
	return s_reward 

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
	return {
		#"turn" : {
		#	"size": 1,
		#	"action_type": "continuous"
		#},        
		#"pitch" : {
		#"size": 1,
		#	"action_type": "continuous"
		#},        		
		"flyTo" : {		
			"action_type": "discrete",						
			"size": 100												
		}				
		
	}

func set_action(action):
	turn_input = action["turn"][0]
	pitch_input = action["pitch"][0]
	
	#env.debug_text.add_text("\nAction:" + str(action)) 

func _physics_process(delta):
	n_steps +=1    
	if n_steps >= MAX_STEPS:
		done = true
		needs_reset = true

	if needs_reset:
		needs_reset = false
		reset()
		return
	
	if cur_goal == null:
		reset()
		
	set_input()
	
	
	# Rotate the transform based checked the input values
	transform.basis = transform.basis.rotated(transform.basis.x.normalized(), pitch_input * pitch_speed * delta)
	transform.basis = transform.basis.rotated(Vector3.UP, turn_input * turn_speed * delta)	
	
	$PlaneModel.rotation.z = lerp($PlaneModel.rotation.z, -float(turn_input) * 0.75, turn_speed * delta)
	$PlaneModel.rotation.x = lerp($PlaneModel.rotation.x, -float(pitch_input), level_speed * delta)

	# Movement is always forward
	velocity = -transform.basis.z.normalized() * max_flight_speed
	# Handle landing/taking unchecked
	set_velocity(velocity)
	set_up_direction(Vector3.UP)
	move_and_slide()
	n_steps += 1
		
	update_reward()
		
func zero_reward():
	reward = 0.0  
	
func set_input():
	#print(_heuristic)
	if _heuristic == "model":
		return
	
	if _heuristic == "human":
		turn_input = Input.get_action_strength("roll_left") - Input.get_action_strength("roll_right")
		pitch_input = Input.get_action_strength("pitch_up") - Input.get_action_strength("pitch_down")
	
	if _heuristic == "AP":		
		var targetHdg = aspect_to_obj(cur_goal)									
		var goal_vector = to_local(cur_goal.position)
		var goal_distance = goal_vector.length()
		
		if AP_mode == "GoTo": 
														
			if goal_distance > 3:			
				turn_input = (targetHdg / abs(1 if targetHdg == 0 else targetHdg)) * (0.85 + (clamp(20 / goal_distance, 0,1))) * clamp(abs(targetHdg), 0.0 , 1.0)  
				#if turn_input < 0.1:
				#	turn_input = 0.0
		
		if AP_mode == "Hold":
			
			if holdStatus == 0:
				if goal_distance > 10:			
					turn_input = (targetHdg / abs(1 if targetHdg == 0 else targetHdg)) * (0.75 + (clamp(20 / goal_distance, 0,1))) * clamp(abs(targetHdg), 0.0 , 1.0)  				
				else:
					holdStatus = 1
			elif holdStatus == 1:
				if goal_distance < 50:
					turn_input = 0
				else:
					holdStatus = 0	
				
func goal_reached(goal):
	
	if goal == cur_goal:
		reward += 100.0
				
		if goal.get_meta('id') != 0:
			env.goalsPending.remove_at(env.goalsPending.find(goal.get_meta('id')))
			#goal.visible = false		
			goal.material = goal.material2
			
			tasksDoneViewer.text = str(len(env.goalsPending)) + " / " + str(len(env.goals))
			
			if len(env.goalsPending) == 0:
				done = true
				tasksDoneViewer.text = "ALL DONE"
								
				
		#print("Next Target")
		cur_goal = null#env.get_next_goal(cur_goal)
		if len(env.goals) > 1:
			
			var auxGoals = env.goalsPending.duplicate()
			
			while cur_goal == null and len(auxGoals) > 0: 
				
				var randIndex = env.rng.randi_range(0,len(auxGoals)-1)
				var index_nextGoal = auxGoals[randIndex]
				auxGoals.remove_at(randIndex)
				#print(index_nextGoal)
				if env.goals[index_nextGoal][1] == -1:
					cur_goal = env.goals[index_nextGoal][0]
					env.goals[index_nextGoal][1] = get_meta('id')
					break	
			if len(auxGoals) == 0:
				cur_goal = env.goals[0][0]
				AP_mode = "Hold"
				#print("Mode == Hold")					
		else:
			cur_goal = env.goals[0][0]
			AP_mode = "Hold"
			#print("Mode == Hold")
	
func exited_game_area():
	done = true
	reward -= 10.0
	exited_arena = true
	reset()

#Kur Functions
func aspect_to_obj(obj):
	#var hdg  = (vec1 - vec2).normalized()	
	#var rad = Vector2($PlaneModel.global_position.x, $PlaneModel.global_position.z).angle_to(Vector2(obj.global_position.x, obj.global_position.z))	
	#var hdg = $PlaneModel.global_transform.basis.get_euler().y
	var hdgO = 0;
	var goal_vector = to_local(obj.position)
	
	if goal_vector.x != 0:
		hdgO  = Vector2(goal_vector.x, goal_vector.z).angle_to(Vector2.UP)	
		#print(hdgO)
		return rad_to_deg(hdgO)
	
	return 0.0
	#print(rad_to_deg(rad))#rad_to_deg($PlaneModel.global_transform.basis.get_euler().y))
	#print(rad * 57.8, " ||||| " ,hdg * 57.8, "  --- ", rad_to_deg(rad - hdg))
									
