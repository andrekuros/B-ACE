extends CanvasLayer

@onready var btn_speed_up = get_node("Control/btn_speedUp")
var blue_score = 0
var red_score = 0

func update_results(results):
	var text = ""
	for result in results:
		text += str(result) + "\n"
	$Control/LastResults.text = text

func update_tactics(tactics):
	var text = ""
	for tactic in tactics:
		text += tactic + "\n"
	$Control/Tactics.text = text
	
func update_scores(_blue_score, _red_score):
	red_score += _red_score
	blue_score += _blue_score
	$Control/Red_Score.text = str(red_score)
	$Control/Blue_Score.text = str(blue_score)
