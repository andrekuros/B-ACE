extends Area3D

@onready var fighter = get_parent()

const Track = preload("res://Sim_assets.gd").Track
const Calc = preload("res://Calc.gd")  # Ensure you have a Calc script for calculations

var pending_tracks_to_add = {}
var pending_tracks_to_remove = []
var debounce_frames = 100  # Number of physics frames to wait for debouncing
var current_debounce_frame = 0  # Current frame counter for debouncing


func _physics_process(delta):
	if current_debounce_frame > 0:
		current_debounce_frame -= 1
		if current_debounce_frame == 0:
			_process_debounce()  # Process debounce when counter reaches 0

func _on_radar_area_entered(area):
	var track_obj = area.get_parent()
	var track_id = track_obj.get_meta("id")
	
	if track_obj.is_type("Fighter") and track_obj.team_color != fighter.team_color:
		var radial = Calc.get_hdg_2d(fighter.position, track_obj.position)
		var dist = fighter.global_transform.origin.distance_to(track_obj.global_transform.origin)
		pending_tracks_to_add[track_id] = {"obj": track_obj, "dist": dist, "radial": radial}			
	current_debounce_frame = debounce_frames
	

func _on_radar_area_exited(area):
	var track_obj = area.get_parent()
	if track_obj.is_type("Fighter") and track_obj.team_color != fighter.team_color:
		var track_id = track_obj.get_meta("id")
		if track_id not in pending_tracks_to_remove:
			pending_tracks_to_remove.append(track_id)
	
	# Set the debounce frame counter
	current_debounce_frame = debounce_frames

func _process_debounce():	
	# Process pending tracks to add
	for track_id in pending_tracks_to_add.keys():
		var data = pending_tracks_to_add[track_id]
		if not fighter.radar_track_list.has(track_id):
			var new_track = Track.new(track_id, data["obj"], data["dist"], data["radial"], true)
			fighter.radar_track_list[track_id] = new_track
		else:
			fighter.reacquired_track(track_id, data["radial"], data["dist"])
	
	# Clear the dictionary after processing
	pending_tracks_to_add.clear()
	
	# Process pending tracks to remove
	for track_id in pending_tracks_to_remove.duplicate():
		if track_id not in pending_tracks_to_add:
			fighter.remove_track(track_id)
			pending_tracks_to_remove.erase(track_id)


func _on_body_entered(body):	
	var track_obj = body
	var track_id = track_obj.get_meta("id")
	
	if track_obj.is_type("Fighter") and track_obj.team_color != fighter.team_color:
		var radial = Calc.get_hdg_2d(fighter.position, track_obj.position)
		var dist = fighter.global_transform.origin.distance_to(track_obj.global_transform.origin)
		pending_tracks_to_add[track_id] = {"obj": track_obj, "dist": dist, "radial": radial}			
	current_debounce_frame = debounce_frames
	

func _on_body_exited(body):	
	var track_obj = body
	if track_obj.is_type("Fighter") and track_obj.team_color != fighter.team_color:
		var track_id = track_obj.get_meta("id")
		if track_id not in pending_tracks_to_remove:
			pending_tracks_to_remove.append(track_id)
	
	# Set the debounce frame counter
	current_debounce_frame = debounce_frames
