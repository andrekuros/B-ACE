extends Window

var obs_vbox
var action_vbox

var selected_agent = 0

@onready var selected_agent_control = $Control/AgentSelector


func _ready():
	obs_vbox = find_child("ObsData")  # Find the VBoxContainer
	action_vbox = find_child("ActionData")  # Find the VBoxContainer
	
	#queue_free_children(action_vbox)  # Clear existing UI elements
	#queue_free_children(obs_vbox)  # Clear existing UI elements
	
	
func initialize(obs_labels, obs, actions_labels, actions):
		
	for i in range(len(obs)):

		var hbox = HBoxContainer.new()  # Create a container for each entry
		var key_label = Label.new()  # Label for the key
		key_label.text = obs_labels[i]
		var value_label = Label.new()  # Label for the value
		value_label.text = str(obs[i])
		
		hbox.add_child(key_label)
		hbox.add_child(value_label)
		obs_vbox.add_child(hbox)  # Add the hbox
	
	
	for i in range(len(actions)):

		var hbox = HBoxContainer.new()  # Create a container for each entry
		var key_label = Label.new()  # Label for the key
		key_label.text = actions_labels[i]
		var value_label = Label.new()  # Label for the value
		value_label.text = str(actions[i])
		
		hbox.add_child(key_label)
		hbox.add_child(value_label)
		action_vbox.add_child(hbox)  # Add the hbox
		
	
func update_obs(obs):
	var i = 0  # Index to keep track of the current obs item
	for hbox in obs_vbox.get_children():
		if i >= obs.size():  # Prevent index out of bounds
			break
		var value_label = hbox.get_child(1) as Label  # Assuming second child is the value label
		value_label.text = str(obs[i])
		i += 1


func update_actions(actions):
	var i = 0  # Index for current action item
	for hbox in action_vbox.get_children():
		if i >= actions.size():  # Prevent index out of bounds
			break
		var value_label = hbox.get_child(1) as Label  # Assuming second child is the value label
		value_label.text = str(actions[i])
		i += 1
		
func queue_free_children(container: Control):
	# Utility function to clear VBoxContainer children
	for child in container.get_children():
		container.remove_child(child)
		child.queue_free()
