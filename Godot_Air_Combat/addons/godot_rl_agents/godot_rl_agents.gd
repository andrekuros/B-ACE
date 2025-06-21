@tool
extends EditorPlugin


func _enter_tree():
	# Initialization of the plugin goes here.
	# Add the new type with a name, a parent type, a script and an icon.
	add_custom_type("Sync", "Node", preload("sync.gd"), preload("icon.png"))
	add_custom_type("B_ACE_sync", "Node", preload("B_ACE_sync.gd"), preload("icon.png"))


func _exit_tree():
	# Clean-up of the plugin goes here.
	# Always remember to remove it from the engine when deactivated.
	remove_custom_type("Sync")
	remove_custom_type("B_ACE_sync")
