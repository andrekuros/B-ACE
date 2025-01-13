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
var move_speed = 5000

var fighterObj = preload("res://components/Fighter.tscn")
const SConv   = preload("res://assets/Sim_assets.gd").SConv

var rng = RandomNumberGenerator.new()


@export var box_size: Vector3 = Vector3(10000, 1, 10000)  # Size of the CSGBox
@export var grid_spacing: int =  500  # Distance between grid lines

func _ready():
	cameraGlobal = $CameraGlobal	
	cameraGlobal.make_current()
	#cameraGlobal.position.y = zoom_level
	
	var grid_mesh = ImmediateMesh.new()
	draw_grid(grid_mesh)
	
	# Create a MeshInstance3D to display the grid
	var csg_box = $CSGBox3D
	csg_box.size = box_size
	
	var grid_instance = MeshInstance3D.new()
	grid_instance.mesh = grid_mesh
	grid_instance.material_override = create_grid_material()
	add_child(grid_instance)
	

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
			cameraGlobal.rotation_degrees = Vector3(-35, 0, 0)
			cameraGlobal.position = Vector3(0, 1000, 1400)
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
				sim.update_scale(1.5)
		
		if event.pressed and event.keycode == KEY_S:
			#cameraGlobal.position.y += zoom_level
			for sim in get_node("SimManager").get_children():				
				sim.update_scale(0.75)
		
		if Input.is_action_pressed("Pause"):			
			get_tree().paused = not get_tree().paused	
			
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
		move_vec.x -= move_speed / Performance.get_monitor(Performance.TIME_FPS)		
	elif Input.is_action_pressed("ui_right"):
		move_vec.x += move_speed / Performance.get_monitor(Performance.TIME_FPS)
	elif Input.is_action_pressed("ui_up"):
		move_vec.z -= move_speed / Performance.get_monitor(Performance.TIME_FPS)
	elif Input.is_action_pressed("ui_down"):
		move_vec.z += move_speed / Performance.get_monitor(Performance.TIME_FPS)
	elif Input.is_action_pressed("ui_page_up"):
		move_vec.y += move_speed / Performance.get_monitor(Performance.TIME_FPS)
	elif Input.is_action_pressed("ui_page_down"):
		move_vec.y -= move_speed / Performance.get_monitor(Performance.TIME_FPS)

	if move_vec.length() == 5000:
		return
	# Adjust the camera movement vector based on the camera's orientation
	move_vec = move_vec.rotated(Vector3.UP, cam.global_transform.basis.get_euler().y)
	cam.global_position += move_vec * delta
	
func draw_grid(mesh: ImmediateMesh):
	var half_size = box_size / 2

	mesh.surface_begin(Mesh.PRIMITIVE_LINES)

	# Draw grid on the XZ plane
	for x in range(-half_size.x, half_size.x + grid_spacing, grid_spacing):		
		mesh.surface_add_vertex(Vector3(x, -100, -half_size.z))
		mesh.surface_add_vertex(Vector3(x, -100, half_size.z))

	for z in range(-half_size.z, half_size.z + grid_spacing, grid_spacing):		
		mesh.surface_add_vertex(Vector3(-half_size.x, -100, z))
		mesh.surface_add_vertex(Vector3(half_size.x, -100, z))

	create_cross()

	mesh.surface_end()
func create_cross():
	var cross_size = 100  # Length of each arm
	var thickness = 2    # Thickness of each arm

	# Create a shared material for both arms
	var material = StandardMaterial3D.new()
	material.albedo_color = Color(0.3, 0.3, 0.3, 0.8)  # Red color with 50% transparency
	material.flags_transparent = true  # Enable transparency
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA  # Use alpha transparency

	# Create the X-axis line using a BoxMesh
	var x_arm = MeshInstance3D.new()
	var x_mesh = BoxMesh.new()
	x_mesh.size = Vector3(cross_size * 2, thickness, thickness)  # Long in X, thick in Y and Z
	x_arm.mesh = x_mesh
	x_arm.material_override = material  # Apply the material
	x_arm.transform.origin = Vector3(0, -100, 0)  # Set position for the X-arm
	add_child(x_arm)

	# Create the Z-axis line using a BoxMesh
	var z_arm = MeshInstance3D.new()
	var z_mesh = BoxMesh.new()
	z_mesh.size = Vector3(thickness, thickness, cross_size * 2)  # Long in Z, thick in X and Y
	z_arm.mesh = z_mesh
	z_arm.material_override = material  # Apply the material
	z_arm.transform.origin = Vector3(0, -100, 0)  # Set position for the Z-arm
	add_child(z_arm)

func create_grid_material() -> StandardMaterial3D:
	var material = StandardMaterial3D.new()
	material.flags_unshaded = true  # Prevent lighting effects
	material.vertex_color_use_as_albedo = true  # Use vertex colors for rendering
	material.flags_transparent = true  # Disable transparency for the grid
	material.albedo_color = Color(0.3, 0.3, 0.3, 0.3)  # Set your desired grid color (pure white as an example)
	return material

