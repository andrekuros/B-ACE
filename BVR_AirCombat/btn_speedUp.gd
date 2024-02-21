extends Button

var speed_option = [0.5, 1 , 5 ,10 , 50, 200]
var speedIdx = 1

# Called when the node enters the scene tree for the first time.
func _ready():
	pass # Replace with function body.

func _on_button_down():
	
	speedIdx = speedIdx + 1
	if speedIdx >= len(speed_option):
		speedIdx = 0	
	
	Engine.physics_ticks_per_second = speed_option[speedIdx] * 20  # Replace with function body.
	Engine.time_scale = speed_option[speedIdx]
	set_text(str(speed_option[speedIdx]) + "X")	
	#set_pressed_no_signal(false)
