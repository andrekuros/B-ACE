extends Area3D

@onready var fighter = get_parent()

const Track = preload("res://assets/Sim_assets.gd").Track
const Calc = preload("res://assets/Calc.gd") # Ensure you have a Calc script for calculations

func _on_radar_area_entered(area):
	var track_obj = area.get_parent()
	var track_id = track_obj.get_meta("id")

	if track_obj.is_type("Fighter") and track_obj.team_color != fighter.team_color:
		
		if not fighter.radar_track_list.has(track_id):
			var new_track = Track.new(track_id, fighter, track_obj)
			fighter.radar_track_list[track_id] = new_track
		else:
			fighter.reacquired_track(fighter, track_obj)

func _on_radar_area_exited(area):
	var track_obj = area.get_parent()

	if track_obj.is_type("Fighter") and track_obj.team_color != fighter.team_color:
		var track_id = track_obj.get_meta("id")
		fighter.remove_track(track_id)

func _on_body_entered(body):
	var track_obj = body
	var track_id = track_obj.get_meta("id")
	
	if track_obj.is_type("Fighter") and track_obj.team_color != fighter.team_color:		
		#print(" Detected by " ,get_meta("id") ," - ",  track_id)
		if not fighter.radar_track_list.has(track_id):
			var new_track = Track.new(track_id, fighter, track_obj)
			fighter.radar_track_list[track_id] = new_track
		else:
			fighter.reacquired_track(track_id)

func _on_body_exited(body):
	var track_obj = body

	if track_obj.is_type("Fighter") and track_obj.team_color != fighter.team_color:
		var track_id = track_obj.get_meta("id")
		fighter.remove_track(track_id)
