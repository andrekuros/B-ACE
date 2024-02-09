extends CSGSphere3D

@onready var env = get_tree().root.get_node("FlyBy")
var material2 = null

func _ready():
	material2 = material.duplicate()
	material2.albedo_color = Color(1, 1, 1) # This will set the color to white

func _on_Area_body_entered(body):
	body.goal_reached(self)
	
	var time_now = Time.get_unix_time_from_system()
	var time_elapsed = time_now - env.time_start
	#OS.get_ticks_msec()
	
	env.numTasksDone = env.numTasksDone + 1
		
	# Next, set the albedo color of the material to a new color
	#

	#if env.numTasksDone % 1 == 0:
	#	print("Chegou ( ", env.numTasksDone, "): " , time_elapsed)
		
	
	
