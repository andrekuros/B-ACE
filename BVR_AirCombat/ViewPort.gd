extends SubViewport

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
var zoom_level = 1500
var move_speed = 30
var fighterObj = preload("res://components/Fighter.tscn")
var rng = RandomNumberGenerator.new()
var numTasksDone = 0

func _ready():
	cameraGlobal = $CameraGlobal	
	cameraGlobal.make_current()
	#cameraGlobal.position.y = zoom_level

func _input(event):	
	if event is InputEventKey:
		if event.pressed and event.keycode == KEY_E:
			# Reset camera view
			cameraGlobal.rotate_x(deg_to_rad(-10.0))	
		
		if event.pressed and event.keycode == KEY_D:
			# Reset camera view
			cameraGlobal.rotate_x(deg_to_rad(10.0))			
			
		
		if event.pressed and event.keycode == KEY_F:
			# Reset camera view
			cameraGlobal.rotation_degrees = Vector3(0, 1, 0)
			cameraGlobal.position = Vector3(0, 500, 1500)
			camera_angle_v = 0
			camera_angle_h = 0
		
		if event.pressed and event.keycode == KEY_C:
			# Reset camera view
			cameraGlobal.make_current()
			cameraGlobal.rotation_degrees = Vector3(-90, 0, 0)
			cameraGlobal.position = Vector3(0, 2500, 0)
			camera_angle_v = 0
			camera_angle_h = 0
			
		if event.pressed and event.keycode == KEY_W:			
			#cameraGlobal.position.y += zoom_level
			for sim in get_node("SimManager").get_children():												
				sim.update_scale(2.0)
		
		if event.pressed and event.keycode == KEY_S:
			#cameraGlobal.position.y += zoom_level
			for sim in get_node("SimManager").get_children():				
				sim.update_scale(0.5)
		

	if event is InputEventMouseMotion:
		var cam = get_camera_3d()
		
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
			cameraGlobal.position.y += zoom_level

	if Input.is_action_just_pressed("CameraNext"):
		if uavCamId + 1 < len(uavs):
			uavCamId = uavCamId + 1
			cameraUav = uavs[uavCamId].get_node("Camera3D")
			cameraUav.make_current()
		else:
			cameraUav = uavs[0].get_node("Camera3D")
			cameraUav.make_current()
			uavCamId = 0

func _process(delta):
	# Movement logic based on arrow key input
	var move_vec = Vector3.ZERO
	var cam = get_camera_3d()
	if Input.is_action_pressed("ui_left"):
		move_vec.x -= move_speed
	elif Input.is_action_pressed("ui_right"):
		move_vec.x += move_speed
	elif Input.is_action_pressed("ui_up"):
		move_vec.z -= move_speed
	elif Input.is_action_pressed("ui_down"):
		move_vec.z += move_speed
	elif Input.is_action_pressed("ui_page_up"):
		move_vec.y += move_speed
	elif Input.is_action_pressed("ui_page_down"):
		move_vec.y -= move_speed

	# Adjust the camera movement vector based on the camera's orientation
	move_vec = move_vec.rotated(Vector3.UP, cam.global_transform.basis.get_euler().y)
	cam.global_position += move_vec * delta
	
