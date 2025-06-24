extends Control

var goals = []
var goalsPending = []
var uavs = []

var cameraGlobal: Camera3D
var cameraUav: Camera3D
var uavCamId = 0

const UAV_CAM_SCALE_VECTOR = Vector3(3.0, 3.0, 3.0)
const GLOBAL_CAM_SCALE_VECTOR = Vector3(5.0, 5.0, 5.0)

var mouse_sens = 0.1
var camera_angle_v = 0
var camera_angle_h = 0

var zoom_level = 10
var move_speed = 5

@onready var canvas = get_node("CanvasLayer")
var fighterObj = preload("res://components/Fighter.tscn")

var rng = RandomNumberGenerator.new()
var numTasksDone = 0

func _ready():	
	
	cameraGlobal = get_node("CameraGlobal")
	cameraGlobal.make_current()
	self.position.y = zoom_level
	RenderingServer.render_loop_enabled = false
