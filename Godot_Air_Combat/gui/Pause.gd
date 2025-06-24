extends Button
var btn_activated = false

func _on_pressed():
		
	if not btn_activated:		
		get_tree().paused = true		
		btn_activated = true		
					
	else:	
		get_tree().paused = false				
		btn_activated = false	
		release_focus()
