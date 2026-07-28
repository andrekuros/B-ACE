extends Node3D

func _ready():
	var mesh_instance = MeshInstance3D.new()
	self.add_child(mesh_instance)
	
	var st = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	
	# Triangle vertices
	var top_vertex = Vector3(0, 0, 1) # Top of the cone
	var base_radius = 0.5 # Radius of the base of the cone
	var height = 1.0 # Height of the cone
	var segments = 120 # Number of segments for smoothness
	
	# Calculate rotation angle
	var angle_step = TAU / segments
	var angle = 0.0
	
	for i in range(segments + 1):
		var dir = Vector3(cos(angle), sin(angle), 0) * base_radius
		var base_vertex1 = dir + Vector3(0, 0, 0) # Base vertex 1
		angle += angle_step
		dir = Vector3(cos(angle), sin(angle), 0) * base_radius
		var base_vertex2 = dir + Vector3(0, 0, 0) # Base vertex 2
		
		# Add top triangle
		st.add_vertex(top_vertex)
		st.add_vertex(base_vertex2)
		st.add_vertex(base_vertex1)
		
		# Add base triangle to close the base
		if i < segments:
			st.add_vertex(base_vertex1)
			st.add_vertex(base_vertex2)
			st.add_vertex(Vector3(0, 0, 0)) # Center of the base

	st.generate_normals()
	var mesh = st.commit()
	mesh_instance.mesh = mesh
