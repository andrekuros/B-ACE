extends CanvasLayer

@onready var btn_speed_up = get_node("Control/btn_speedUp")

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
