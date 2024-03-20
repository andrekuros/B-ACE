# SimulationThread.gd
extends Thread

var simulation
var simulation_args

func _init(sim, args):
	simulation = sim
	simulation_args = args

func _run():
	simulation.initialize(simulation_args)
	while !simulation.is_done():		
		simulation.process(get_process_delta_time())
