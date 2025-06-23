extends Button

@onready var b_ace_synv = get_tree().root.get_node("B_ACE").get_node("B_ACE_sync")

var speed_option = [1 , 10 , 50, 200, 1000]
var speedIdx = 1

func _on_button_down():
	
	speedIdx = speedIdx + 1
	if speedIdx >= len(speed_option):
		speedIdx = 0	
	
	Engine.physics_ticks_per_second = speed_option[speedIdx] * 20  # Replace with function body.
	Engine.time_scale = speed_option[speedIdx]
		
	set_text(str(speed_option[speedIdx]) + "X")	
	b_ace_synv.speed_up = speed_option[speedIdx]
