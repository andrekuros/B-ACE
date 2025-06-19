extends CheckButton

var btn_activated = false
# Called every frame. 'delta' is the elapsed time since the previous frame.

func _on_button_down():
	
	if not btn_activated:
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED)
		btn_activated = true
	else:
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
		btn_activated = false
