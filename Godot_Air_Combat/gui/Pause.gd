extends Button

var btn_activated = false
# Called every frame. 'delta' is the elapsed time since the previous frame.

func _on_pressed():
			
	if not btn_activated:
		get_tree().paused = true
		# Also pause our manual render timer so the screen freezes
#		if has_node("RenderTimer"):
#			get_node("RenderTimer").paused = true
		btn_activated = true
	else:
		get_tree().paused = false		
		# Resume our manual render timer
#		if has_node("RenderTimer"):
#			get_node("RenderTimer").paused = false
		btn_activated = false

