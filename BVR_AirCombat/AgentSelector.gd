extends HBoxContainer

@onready var debug_window = get_parent().get_parent()
	
func create_agent_buttons(num_agents):
	for agent_idx in range(num_agents):
		var button = Button.new()
		button.text = str(agent_idx)
		# Use the recommended Signal.connect() with an implicit Callable for the defined function.
		# Bind the agent_idx as an argument to the callable method.
		button.pressed.connect(_on_agent_button_pressed.bind(agent_idx))
		add_child(button)



func _on_agent_button_pressed(agent_idx):
	# This method is called when an agent button is pressed
	# Now 'agent_idx' is directly accessible as a parameter
	debug_window.selected_agent = agent_idx
	


	
