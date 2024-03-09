extends Node3D

var goals = []
var goalsPending = []
var uavs = []

var cameraGlobal: Camera3D
var cameraUav: Camera3D
var uavCamId = 0

const UAV_CAM_SCALE_VECTOR = Vector3(3.0, 3.0, 3.0)
const GLOBAL_CAM_SCALE_VECTOR = Vector3(5.0, 5.0, 5.0)

var mouse_sens = 0.1
var camera_angle_v = 0
var camera_angle_h = 0

var zoom_level = 10
var move_speed = 5

@onready var canvas = get_node("CanvasLayer")
var fighterObj = preload("res://Fighter.tscn")

var rng = RandomNumberGenerator.new()
var numTasksDone = 0

func _ready():	
	goals.append([$Goals.get_children()[0], -1])
	cameraGlobal = get_node("CameraGlobal")
	cameraGlobal.make_current()
	self.position.y = zoom_level
	look_at(Vector3.ZERO, Vector3.UP)

func get_next_goal(current_goal):
	if current_goal == null:
		return goals[0][0]
	for i in range(len(goals) - 1):
		if goals[i][0] == current_goal:
			return goals[(i + 1) % len(goals)][0]
	return null

func get_last_goal():
	return goals[-1][0]

func _input(event):
	if event is InputEventKey:
		if event.pressed and event.keycode == KEY_F:
			# Reset camera view
			cameraGlobal.rotation_degrees = Vector3(0, 1, 0)
			cameraGlobal.position = Vector3(0, 500, 1500)
			camera_angle_v = 0
			camera_angle_h = 0
			
	if event is InputEventMouseMotion:
		var cam = get_viewport().get_camera_3d()
		if Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
			cam.rotate_y(deg_to_rad(-event.relative.x * mouse_sens))
			var change_v = -event.relative.y * mouse_sens
			camera_angle_v += change_v
			cam.rotate_x(deg_to_rad(change_v))
		elif Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
			# Rotate camera around its forward vector (for inclination)
			var change_h = event.relative.x * mouse_sens
			camera_angle_h += change_h
			cam.rotate(cam.transform.basis.z, deg_to_rad(change_h))

	elif event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
			zoom_level = -25
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
			zoom_level = 25
		#zoom_level = clamp(zoom_level, 5, 50)
		cameraGlobal.position.y += zoom_level

	if Input.is_action_just_pressed("CameraNext"):
		if uavCamId + 1 < len(uavs): 
			uavCamId = uavCamId + 1			
			cameraUav =  uavs[uavCamId].get_node("Camera3D")
			#debug_text.add_text("\n" + uavs[uavCamId]._heuristic + " - " + uavs[uavCamId].AP_mode)
			cameraUav.make_current()
		else:
			cameraUav = uavs[0].get_node("Camera3D")
			cameraUav.make_current()
			uavCamId = 0			

func _process(delta):
	# Movement logic based on arrow key input
	var move_vec = Vector3.ZERO
	var cam = get_viewport().get_camera_3d()
	if Input.is_action_pressed("ui_left"):
		move_vec.x -= move_speed
	elif Input.is_action_pressed("ui_right"):
		move_vec.x += move_speed
	elif Input.is_action_pressed("ui_up"):
		move_vec.z -= move_speed
	elif Input.is_action_pressed("ui_down"):
		move_vec.z += move_speed
	# Adjust the camera movement vector based on the camera's orientation
	move_vec = move_vec.rotated(Vector3.UP, cam.global_transform.basis.get_euler().y)	
	cam.global_position += move_vec * delta
