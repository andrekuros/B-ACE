extends VBoxContainer

const SConv = preload("res://Figther_assets.gd").SConv


func _ready():
	# Initial setup if needed
	pass


func update_uav_data(action, max_g):
	
	#var hdg_input = action["hdg_input"] * 180.0
	#var level_input = (action["level_input"] * 22500.0 + 27500.0) * SConv.FT2GDM
	#var desiredG_input = (action["desiredG_input"] * (max_g - 1.0) + (max_g + 1.0)) / 2.0
	#var shoot_input = 0 if action["shoot_input"] <= 0 else 1
	pass
	#var hdg_input = action[0] * 180.0		
	#var level_input = (action[1] * 22500.0 + 27500.0) * SConv.FT2GDM  	
	#var desiredG_input = (action[2] * (max_g  - 1.0) + (max_g + 1.0))/2.0	
	#var shoot_input = 0 if action[3] <= 0 else 1
#
	#level_input_label.text = "Level Input: %s" % str(level_input)
	#hdg_input_label.text = "Heading Input: %s" % str(hdg_input)
	#desiredG_input_label.text = "Desired G Input: %s" % str(desiredG_input)
	#shoot_input_label.text = "Shoot Input: %s" % str(shoot_input)
