extends CSGSphere3D

@onready var env = get_tree().root.get_node("FlyBy")

var material2 = null

func _ready():
	material2 = material.duplicate()
	material2.albedo_color = Color(1, 1, 1) # This will set the color to white

	
	
