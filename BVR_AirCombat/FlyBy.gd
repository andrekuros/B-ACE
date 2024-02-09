extends Node3D

var goals = Array()
var goalsPending = Array()
var uavs = Array()

var cameraGlobal = null
var cameraUav = null
var uavCamId = 0
var mouse_sens = 0.1
var camera_anglev=0

@onready var debug_text = get_node("CanvasLayer/Control/RichTextLabel")
@onready var canvas = get_node("CanvasLayer")

var fighterObj = preload("res://Fighter.tscn")


var time_start = 0
var time_now = 0
var rng = RandomNumberGenerator.new()
var numTasksDone = 0

var numTasks = 10
var numUav = 1

# Called when the node enters the scene tree for the first time.
func _ready():
	#RenderingServer.render_loop_enabled = false
	
	goals.append([$Goals.get_children()[0], -1])
	#goalsPending.append(0);	
	
	time_start = Time.get_unix_time_from_system()	
		
	cameraGlobal = get_node("CameraGlobal")
	#cameraUav = figtherObj.instantiate().get_node("Camera3D")	
		
	print (cameraUav)
	print (cameraGlobal)	
	cameraGlobal.make_current()
	#Engine.physics_ticks_per_second = 3.0*60 # Replace with function body.
	#Engine.time_scale = 1.0
	#get_tree().set_time_scale(2.0)		

func get_next_goal(current_goal):
	if current_goal == null:#or goals.is_empty():								
		return goals[0][0]
	var index = null
	
	for i in len(goals ) - 1:
		if goals[i][0] == current_goal:
			index = (i+1) % len(goals)
			break
			
	return goals[index][0][0]

func get_last_goal():
	return goals[-1][0]
			
func _input(event):		
	
	if event is InputEventKey:
		if event.pressed and event.keycode == KEY_C:
			if cameraGlobal.current:
				cameraUav =  uavs[uavCamId].get_node("Camera3D")
				cameraUav.make_current()
				debug_text.add_text("\nCamera Changed (1)")
			else:
				cameraGlobal.make_current()	
				debug_text.add_text("\nCamera Changed (2)")
	
	
	if event is InputEventMouseMotion:
		
		if Input.is_mouse_button_pressed( 1 ): # Left click
			var cam = get_viewport().get_camera_3d()
			cam.rotate_y(deg_to_rad(-event.relative.x*2))
			var changev=-event.relative.y*2
			if camera_anglev+changev>-50 and camera_anglev+changev<50:
				camera_anglev+=changev
				cam.rotate_x(deg_to_rad(changev))
		#elif Input.is_mouse_button_pressed( MOUSE_BUTTON_WHEEL_UP ):
	
	if Input.is_action_just_pressed("CameraNext"):		
		
		if uavCamId + 1 < len(uavs): 
			uavCamId = uavCamId + 1			
			cameraUav =  uavs[uavCamId].get_node("Camera3D")
			debug_text.add_text("\n" + uavs[uavCamId]._heuristic + " - " + uavs[uavCamId].AP_mode)
			cameraUav.make_current()
		else:
			cameraUav = uavs[0].get_node("Camera3D")
			cameraUav.make_current()
			uavCamId = 0			
		
							
# Called every frame. 'delta' is the elapsed time since the previous frame.
#func _process(delta):
#    pass


