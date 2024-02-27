extends Node

func _ready():
	DebugGUI.SetGraphProperties(self, "from gdscript", 0.0, 10.0, 1, Color.WHITE, true)
	DebugGUI.Log(self)
	DebugGUI.Log("This can be done from gdscript too!")

func _process(_delta):
	DebugGUI.Graph(self, sin(Time.get_ticks_msec() / 100.0))
