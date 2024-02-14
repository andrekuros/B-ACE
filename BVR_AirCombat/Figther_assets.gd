extends Node


class SConv:
	const SCALE_FACTOR = 100.0
	const REAL2GD = 1.0 / SCALE_FACTOR
	#const REAL2GD = 1 / 200               #GoDot meter represent 200m in real
	const NM2M    = 1852.0 
	const NM2GDM  = 1852.0 / SCALE_FACTOR           #GDM is GoDot Meters
	const KNOT2M_S = 1.0 / 1.944
	const KNOT2GDM_S = 1.0 / (1.944 * SCALE_FACTOR)
	const GDM2NM = SCALE_FACTOR / 1852.0
	const GDM_S2KNOT = 1.944 * SCALE_FACTOR
	const M_S2KNOT = 1.944
	
	const FT2M = 0.3048 
	const FT2GDM = 0.3048 / SCALE_FACTOR
	
	const GRAVITY_GDM = 9.81 * REAL2GD
	
	func _init():
		pass

class Track:
	var id
	var obj
	var dist
	var radial
	var detected

	func _init(id, obj, dist, radial, detected):
		self.id = id
		self.obj = obj
		self.dist = dist
		self.radial = radial
		self.detected = detected
	
	func update_dist_radial(_dist, _radial):
		self.dist = _dist
		self.radial = _radial
	
	func detected_status(_detected):
		self.detected = _detected
		

