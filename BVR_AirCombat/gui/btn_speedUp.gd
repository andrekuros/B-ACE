extends Button

var speed_option = [0.1, 1 , 5 ,10 , 50, 200, 1000]
var speedIdx = 1

func _on_button_down():
	
	speedIdx = speedIdx + 1
	if speedIdx >= len(speed_option):
		speedIdx = 0	
	
	Engine.physics_ticks_per_second = speed_option[speedIdx] * 20  # Replace with function body.
	Engine.time_scale = speed_option[speedIdx]
	
	#ProjectSettings.set_setting("application/config/target_fps", Engine.physics_ticks_per_second)		
	set_text(str(speed_option[speedIdx]) + "X")	
	#set_pressed_no_signal(false)
