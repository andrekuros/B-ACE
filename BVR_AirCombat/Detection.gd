extends Area3D

@onready var figther = get_parent()

const Track = preload("res://Figther_assets.gd").Track

# Called when the node enters the scene tree for the first time.
func _ready():
	#fighter = get_parent()
	pass # Replace with function body.

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta):
	pass


func _on_radar_area_entered(area):
	#print("Detect from ", get_parent().get_meta("id"))
	
	var track_obj = area.get_parent()	
	var track_id = track_obj.get_meta("id")
	
	if track_obj.is_type("Fighter") and track_obj.team_color != figther.team_color: 				
			
		var radial = figther.aspect_to_obj(track_obj)
		var dist = figther.to_local(track_obj.position).length()			
			
		if not figther.radar_track_list.has(track_id):		
			var new_track = Track.new(track_id, track_obj, dist, radial, true )
			figther.radar_track_list[track_id] = new_track
			#print("NewTrack", track_id, get_parent().get_meta("id"))
		else:
			var track = figther.radar_track_list[track_id]
			track.update_dist_radial(dist, radial)
			track.detected_status(true)
							
			
		
		#fighter.launch_missile_at_target(body)
	
func _on_radar_area_exited(area):
	var track_obj = area.get_parent()	
	# Find the index of the vector to remove
	if track_obj.is_type("Fighter") and track_obj.team_color != figther.team_color: 
		var track_id = area.get_parent().get_meta("id")		
		figther.remove_track(track_id)
				

