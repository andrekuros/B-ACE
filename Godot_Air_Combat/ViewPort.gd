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

var help_popup_scene = preload("res://gui/HelpPopup.tscn")
var help_popup = null

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
		var cam = get_viewport().get_camera_3d()
		
		if event.pressed and event.keycode == KEY_E:
			cam.rotate_x(deg_to_rad(-10.0))			
		if event.pressed and event.keycode == KEY_D:			
			cam.rotate_x(deg_to_rad(10.0))		
		if event.pressed and event.keycode == KEY_PAGEDOWN:
			cam.position +=  Vector3(0,-50,0)			
		if event.pressed and event.keycode == KEY_PAGEUP:			
			cam.position +=  Vector3(0,50,0)
		if event.pressed and event.keycode == KEY_UP:
			cam.position +=  Vector3(0,0,-50)			
		if event.pressed and event.keycode == KEY_DOWN:			
			cam.position +=  Vector3(0,0,50)				
		if event.pressed and event.keycode == KEY_LEFT:			
			cam.position +=  Vector3(-50,0,0)				
		if event.pressed and event.keycode == KEY_RIGHT:			
			cam.position +=  Vector3(50,0,0)				
		
		if event.pressed and event.keycode == KEY_F:
			cam.rotation_degrees = Vector3(-35, 0, 0)
			cam.position = Vector3(0, 1000, 1400)
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
			for sim in get_node("SimManager").get_children():												
				sim.update_scale(1.1)
		
		if event.pressed and event.keycode == KEY_S:
			#cameraGlobal.position.y += zoom_level
			for sim in get_node("SimManager").get_children():				
				sim.update_scale(0.9)	
				
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
		

		if event.pressed and event.keycode == KEY_H:
			if help_popup != null:
				help_popup.queue_free()
				help_popup = null
			else:
				help_popup = help_popup_scene.instantiate()
				add_child(help_popup)
				#help_popup.position = get_tree().root.get_visible_rect().get_center()
						
	
	
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
	material.albedo_color = Color(0.6, 0.6, 0.6, 0.9)  # Red color with 50% transparency
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
	material.albedo_color = Color(0.4, 0.4, 0.4, 0.4)  # Set your desired grid color (pure white as an example)
	return material
