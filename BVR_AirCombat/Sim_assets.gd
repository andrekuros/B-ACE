extends Node

const Calc = preload("res://Calc.gd") # Ensure you have a Calc script for calculations

class EnvConfig:	
	
	const DEFAULT_PHYSICS_FPS := 20
	const DEFAULT_MAX_CYCLES := 36000 #30 * 20 * 60 (30 MINUTES REAL TIME)	
	const DEFAULT_PARALLEL_ENVS := 1
	const DEFAULT_SEED := 1
	const DEFAULT_SPEED_UP := 50000
	const DEFAULT_RENDERIZE := 1
	const DEFAULT_EXPERIMENT_MODE := 0
	const DEFAULT_DEBUG_VIEW := 0
	const DEFAULT_ACTION_REPEAT := 20
	const DEFAULT_ACTION_TYPE := "Low_Level_Discrete"		
	const DEFAULT_FULL_OBSERVATION := 1
	const DEFAULT_ACTIONS_2D := 0
	
	var phy_fps: int
	var max_cycles: int
	var _seed: int
	var parallel_envs: int
	var speed_up: int
	var renderize: int 
	var debug_view: int
	var experiment_mode: int
	var action_type: String
	var action_repeat: int
	var full_observation: int
	var actions_2d: int
		
	func _init(config):				
				
		self.phy_fps 		= int(config.get("phy_fps", DEFAULT_PHYSICS_FPS))
		self.max_cycles 	= int(config.get("max_cycles", DEFAULT_MAX_CYCLES))
		self._seed 			= int(config.get("seed", DEFAULT_SEED))
		self.parallel_envs	= int(config.get("parallel_envs", DEFAULT_PARALLEL_ENVS))
		
		self.speed_up		= int(config.get("speed_up", DEFAULT_SPEED_UP))
		self.renderize		= int(config.get("renderize", DEFAULT_RENDERIZE))
		self.debug_view		= int(config.get("debug_view", DEFAULT_DEBUG_VIEW))
		self.experiment_mode= int(config.get("experiment_mode", DEFAULT_EXPERIMENT_MODE))
		
		self.action_type 	= config.get("action_type", DEFAULT_ACTION_TYPE)
		self.action_repeat 	= int(config.get("action_repeat", DEFAULT_ACTION_REPEAT))
		
		self.full_observation 	= int(config.get("full_observation", DEFAULT_FULL_OBSERVATION))
		self.actions_2d 		= int(config.get("actions_2d", DEFAULT_ACTIONS_2D))
				
	
	func update_config(config):		
		
		self.max_cycles = config.get("max_cycles", self.max_cycles)
		self._seed = config.get("seed", self.seed)
		self.parallel_envs = config.get("parallel_envs", self.parallel_envs)
		self.speed_up = config.get("speed_up", self.speed_up)
		self.renderize = config.get("renderize", self.renderize)
		self.debug_view = config.get("debug_view", self.debug_view)
		self.experiment_mode= config.get("experiment_mode", self.experiment_mode)
		self.action_type = config.get("action_type", self.action_type)
		self.action_repeat = config.get("action_repeat", self.action_repeat)
		self.full_observation = config.get("full_observation", self.full_observation)
		self.actions_2d = config.get("actions_2d", self.actions_2d)
							
class SimConfig:	
		
	const DEFAULT_NUM_ALLIES := 1
	const DEFAULT_NUM_ENEMIES := 1
	const DEFAULT_ENEMIES_BEHAVIOR:= "baseline1"
	const DEFAULT_AGENTS_BEHAVIOR := "baseline1" #wez_eval_shooter
	
	const DEFAULT_RMAX_MODEL := "2076654628949.1245*blue_alt + 12.056060791015625*diffAlt + 3.0914306640625*cosAspect + -0.1983642578125*sinAspect + 1.73046875*cosAngleOff + 0.10888671875*sinAngleOff + -35.2476806640625*blue_alt**2 + -6.3177490234375*blue_alt*diffAlt + 3.72723388671875*blue_alt*cosAspect + 2.304412841796875*blue_alt*sinAspect + 1.2400970458984375*blue_alt*cosAngleOff + -1.28912353515625*blue_alt*sinAngleOff + -17.99517822265625*diffAlt**2 + 8.948974609375*diffAlt*cosAspect + -1.229034423828125*diffAlt*sinAspect + 4.14361572265625*diffAlt*cosAngleOff + 0.794921875*diffAlt*sinAngleOff + 7.788848876953125*cosAspect**2 + 0.34857177734375*cosAspect*sinAspect + -4.484832763671875*cosAspect*cosAngleOff + -0.1380462646484375*cosAspect*sinAngleOff + 6.889312744140625*sinAspect**2 + 0.1212310791015625*sinAspect*cosAngleOff + 3.8235931396484375*sinAspect*sinAngleOff + 8.410614013671875*cosAngleOff**2 + 0.252349853515625*cosAngleOff*sinAngleOff + 6.260711669921875*sinAngleOff**2 + 189.436767578125*blue_alt**3 + 107.62933349609375*blue_alt**2*diffAlt + 52.844482421875*blue_alt**2*cosAspect + -6.945526123046875*blue_alt**2*sinAspect + 20.019058227539062*blue_alt**2*cosAngleOff + 3.559173583984375*blue_alt**2*sinAngleOff + -87.88659763336182*blue_alt*diffAlt**2 + -24.760971069335938*blue_alt*diffAlt*cosAspect + 18.163850784301758*blue_alt*diffAlt*sinAspect + 5.955109596252441*blue_alt*diffAlt*cosAngleOff + -1.6511790752410889*blue_alt*diffAlt*sinAngleOff + -1038327314485.8118*blue_alt*cosAspect**2 + -10.471000671386719*blue_alt*cosAspect*sinAspect + -15.278762817382812*blue_alt*cosAspect*cosAngleOff + 3.6130733489990234*blue_alt*cosAspect*sinAngleOff + -1038327314467.9543*blue_alt*sinAspect**2 + -0.7051506042480469*blue_alt*sinAspect*cosAngleOff + 9.699928283691406*blue_alt*sinAspect*sinAngleOff + -1038327314483.5344*blue_alt*cosAngleOff**2 + -1.356292724609375*blue_alt*cosAngleOff*sinAngleOff + -1038327314470.24*blue_alt*sinAngleOff**2 + 136.47922039031982*diffAlt**3 + 27.957998275756836*diffAlt**2*cosAspect + -8.655871868133545*diffAlt**2*sinAspect + -9.961368560791016*diffAlt**2*cosAngleOff + -2.487596035003662*diffAlt**2*sinAngleOff + 7.298583984375*diffAlt*cosAspect**2 + 6.508277893066406*diffAlt*cosAspect*sinAspect + -3.8415298461914062*diffAlt*cosAspect*cosAngleOff + -2.7787551879882812*diffAlt*cosAspect*sinAngleOff + 4.798301696777344*diffAlt*sinAspect**2 + -0.00328826904296875*diffAlt*sinAspect*cosAngleOff + -4.613254547119141*diffAlt*sinAspect*sinAngleOff + 11.846946716308594*diffAlt*cosAngleOff**2 + 0.6610751152038574*diffAlt*cosAngleOff*sinAngleOff + 0.264678955078125*diffAlt*sinAngleOff**2 + 1.5635452270507812*cosAspect**3 + -0.2617835998535156*cosAspect**2*sinAspect + 0.3662872314453125*cosAspect**2*cosAngleOff + 0.15230560302734375*cosAspect**2*sinAngleOff + 1.549346923828125*cosAspect*sinAspect**2 + -0.3339691162109375*cosAspect*sinAspect*cosAngleOff + 2.7457275390625*cosAspect*sinAspect*sinAngleOff + -2.857158660888672*cosAspect*cosAngleOff**2 + -0.6147308349609375*cosAspect*cosAngleOff*sinAngleOff + 5.997802734375*cosAspect*sinAngleOff**2 + 0.06819915771484375*sinAspect**3 + 1.3641109466552734*sinAspect**2*cosAngleOff + -0.0592193603515625*sinAspect**2*sinAngleOff + -0.0585479736328125*sinAspect*cosAngleOff**2 + 2.662933349609375*sinAspect*cosAngleOff*sinAngleOff + -0.1279449462890625*sinAspect*sinAngleOff**2 + 1.086395263671875*cosAngleOff**3 + 0.037811279296875*cosAngleOff**2*sinAngleOff + 0.6650466918945312*cosAngleOff*sinAngleOff**2 + 0.057952880859375*sinAngleOff**3 + -110.43049049377441*blue_alt**4 + -374.5380916595459*blue_alt**3*diffAlt + -126.92086029052734*blue_alt**3*cosAspect + -15.900655746459961*blue_alt**3*sinAspect + -50.887380838394165*blue_alt**3*cosAngleOff + -16.113043308258057*blue_alt**3*sinAngleOff + 274.4538631439209*blue_alt**2*diffAlt**2 + 146.27089309692383*blue_alt**2*diffAlt*cosAspect + 16.06563711166382*blue_alt**2*diffAlt*sinAspect + 51.40291213989258*blue_alt**2*diffAlt*cosAngleOff + 15.849489510059357*blue_alt**2*diffAlt*sinAngleOff + -14.251876831054688*blue_alt**2*cosAspect**2 + 28.579818725585938*blue_alt**2*cosAspect*sinAspect + 9.159783363342285*blue_alt**2*cosAspect*cosAngleOff + 0.28330421447753906*blue_alt**2*cosAspect*sinAngleOff + -20.96734619140625*blue_alt**2*sinAspect**2 + 3.1692371368408203*blue_alt**2*sinAspect*cosAngleOff + 1.8480148315429688*blue_alt**2*sinAspect*sinAngleOff + -17.36309814453125*blue_alt**2*cosAngleOff**2 + 3.7424869537353516*blue_alt**2*cosAngleOff*sinAngleOff + -17.856475830078125*blue_alt**2*sinAngleOff**2 + 48.632596015930176*blue_alt*diffAlt**3 + -83.27345657348633*blue_alt*diffAlt**2*cosAspect + -20.46155560016632*blue_alt*diffAlt**2*sinAspect + -42.40724563598633*blue_alt*diffAlt**2*cosAngleOff + 9.27934718132019*blue_alt*diffAlt**2*sinAngleOff + -7.10333251953125*blue_alt*diffAlt*cosAspect**2 + -48.59035134315491*blue_alt*diffAlt*cosAspect*sinAspect + -33.11201524734497*blue_alt*diffAlt*cosAspect*cosAngleOff + 2.948246717453003*blue_alt*diffAlt*cosAspect*sinAngleOff + 0.7986373901367188*blue_alt*diffAlt*sinAspect**2 + -2.037494659423828*blue_alt*diffAlt*sinAspect*cosAngleOff + 10.24866008758545*blue_alt*diffAlt*sinAspect*sinAngleOff + -0.7918167114257812*blue_alt*diffAlt*cosAngleOff**2 + -5.823333263397217*blue_alt*diffAlt*cosAngleOff*sinAngleOff + -5.51434326171875*blue_alt*diffAlt*sinAngleOff**2 + 5.97662353515625*blue_alt*cosAspect**3 + 2.0822958946228027*blue_alt*cosAspect**2*sinAspect + -2.5890560150146484*blue_alt*cosAspect**2*cosAngleOff + -2.1821060180664062*blue_alt*cosAspect**2*sinAngleOff + -2.2214012145996094*blue_alt*cosAspect*sinAspect**2 + -0.2612800598144531*blue_alt*cosAspect*sinAspect*cosAngleOff + 7.824872970581055*blue_alt*cosAspect*sinAspect*sinAngleOff + 10.97076416015625*blue_alt*cosAspect*cosAngleOff**2 + 0.5106010437011719*blue_alt*cosAspect*cosAngleOff*sinAngleOff + -7.227508544921875*blue_alt*cosAspect*sinAngleOff**2 + 0.24064064025878906*blue_alt*sinAspect**3 + 3.7694530487060547*blue_alt*sinAspect**2*cosAngleOff + 0.8681716918945312*blue_alt*sinAspect**2*sinAngleOff + 0.9417991638183594*blue_alt*sinAspect*cosAngleOff**2 + -4.547910690307617*blue_alt*sinAspect*cosAngleOff*sinAngleOff + 1.3790931701660156*blue_alt*sinAspect*sinAngleOff**2 + 1.1799125671386719*blue_alt*cosAngleOff**3 + -0.8796977996826172*blue_alt*cosAngleOff**2*sinAngleOff + -0.0067596435546875*blue_alt*cosAngleOff*sinAngleOff**2 + -0.4347419738769531*blue_alt*sinAngleOff**3 + -642.1519951820374*diffAlt**4 + -1.479940414428711*diffAlt**3*cosAspect + 3.2153713703155518*diffAlt**3*sinAspect + 15.169073581695557*diffAlt**3*cosAngleOff + 3.2277870178222656*diffAlt**3*sinAngleOff + -23.70647144317627*diffAlt**2*cosAspect**2 + 25.227389335632324*diffAlt**2*cosAspect*sinAspect + 32.06813144683838*diffAlt**2*cosAspect*cosAngleOff + -1.1652107238769531*diffAlt**2*cosAspect*sinAngleOff + 5.719335556030273*diffAlt**2*sinAspect**2 + 1.285778284072876*diffAlt**2*sinAspect*cosAngleOff + -12.021614074707031*diffAlt**2*sinAspect*sinAngleOff + -11.29319953918457*diffAlt**2*cosAngleOff**2 + 1.7453880310058594*diffAlt**2*cosAngleOff*sinAngleOff + -6.700664520263672*diffAlt**2*sinAngleOff**2 + 3.09014892578125*diffAlt*cosAspect**3 + -0.25733375549316406*diffAlt*cosAspect**2*sinAspect + 9.445121765136719*diffAlt*cosAspect**2*cosAngleOff + 1.6865348815917969*diffAlt*cosAspect**2*sinAngleOff + 5.84228515625*diffAlt*cosAspect*sinAspect**2 + 0.5880584716796875*diffAlt*cosAspect*sinAspect*cosAngleOff + -10.846814155578613*diffAlt*cosAspect*sinAspect*sinAngleOff + -3.9632797241210938*diffAlt*cosAspect*cosAngleOff**2 + 0.3884916305541992*diffAlt*cosAspect*cosAngleOff*sinAngleOff + 12.895729064941406*diffAlt*cosAspect*sinAngleOff**2 + -0.9809226989746094*diffAlt*sinAspect**3 + -5.324823379516602*diffAlt*sinAspect**2*cosAngleOff + -0.8921699523925781*diffAlt*sinAspect**2*sinAngleOff + -0.4622955322265625*diffAlt*sinAspect*cosAngleOff**2 + 1.565011978149414*diffAlt*sinAspect*cosAngleOff*sinAngleOff + -0.7846465110778809*diffAlt*sinAspect*sinAngleOff**2 + 1.9264564514160156*diffAlt*cosAngleOff**3 + 0.8517608642578125*diffAlt*cosAngleOff**2*sinAngleOff + 2.2015380859375*diffAlt*cosAngleOff*sinAngleOff**2 + -0.06324005126953125*diffAlt*sinAngleOff**3 + 2.6662445068359375*cosAspect**4 + 0.18377304077148438*cosAspect**3*sinAspect + -3.2440032958984375*cosAspect**3*cosAngleOff + -0.07891845703125*cosAspect**3*sinAngleOff + 5.087287902832031*cosAspect**2*sinAspect**2 + 0.31053924560546875*cosAspect**2*sinAspect*cosAngleOff + 2.5097198486328125*cosAspect**2*sinAspect*sinAngleOff + 7.277862548828125*cosAspect**2*cosAngleOff**2 + 0.3022308349609375*cosAspect**2*cosAngleOff*sinAngleOff + 0.484771728515625*cosAspect**2*sinAngleOff**2 + 0.189453125*cosAspect*sinAspect**3 + -1.2328948974609375*cosAspect*sinAspect**2*cosAngleOff + -0.086639404296875*cosAspect*sinAspect**2*sinAngleOff + 0.15546417236328125*cosAspect*sinAspect*cosAngleOff**2 + -8.634204864501953*cosAspect*sinAspect*cosAngleOff*sinAngleOff + 0.20786285400390625*cosAspect*sinAspect*sinAngleOff**2 + -2.5988311767578125*cosAspect*cosAngleOff**3 + -0.04668426513671875*cosAspect*cosAngleOff**2*sinAngleOff + -1.8989105224609375*cosAspect*cosAngleOff*sinAngleOff**2 + -0.1175994873046875*cosAspect*sinAngleOff**3 + 1.8147430419921875*sinAspect**4 + -0.16738128662109375*sinAspect**3*cosAngleOff + 1.3438568115234375*sinAspect**3*sinAngleOff + 1.111419677734375*sinAspect**2*cosAngleOff**2 + -0.07708740234375*sinAspect**2*cosAngleOff*sinAngleOff + 5.795036315917969*sinAspect**2*sinAngleOff**2 + 0.08251953125*sinAspect*cosAngleOff**3 + 1.8575210571289062*sinAspect*cosAngleOff**2*sinAngleOff + 0.09781646728515625*sinAspect*cosAngleOff*sinAngleOff**2 + 1.9542999267578125*sinAspect*sinAngleOff**3 + 3.478057861328125*cosAngleOff**4 + 0.12640380859375*cosAngleOff**3*sinAngleOff + 4.924713134765625*cosAngleOff**2*sinAngleOff**2 + 0.09942626953125*cosAngleOff*sinAngleOff**3 + 1.395294189453125*sinAngleOff**4"	
	const DEFAULT_RNEZ_MODEL := "96869445529.47823*blue_alt + 9.628267288208008*diffAlt + 5.729976654052734*cosAspect + 0.5104331970214844*sinAspect + 0.2366771697998047*cosAngleOff + 0.22320938110351562*sinAngleOff + 8.278057098388672*blue_alt**2 + -57.100215911865234*blue_alt*diffAlt + -5.616024017333984*blue_alt*cosAspect + 1.1545791625976562*blue_alt*sinAspect + 0.4416494369506836*blue_alt*cosAngleOff + 2.970865249633789*blue_alt*sinAngleOff + 3.2237682342529297*diffAlt**2 + 15.492634773254395*diffAlt*cosAspect + -1.670405387878418*diffAlt*sinAspect + 2.4065818786621094*diffAlt*cosAngleOff + -2.7067794799804688*diffAlt*sinAngleOff + 3.4095516204833984*cosAspect**2 + -0.6418371200561523*cosAspect*sinAspect + -0.6781635284423828*cosAspect*cosAngleOff + -0.33744144439697266*cosAspect*sinAngleOff + 5.524140357971191*sinAspect**2 + -5.626678466796875e-05*sinAspect*cosAngleOff + 0.5367240905761719*sinAspect*sinAngleOff + 4.727092742919922*cosAngleOff**2 + -0.019608497619628906*cosAngleOff*sinAngleOff + 4.209268569946289*sinAngleOff**2 + -154.2113857269287*blue_alt**3 + 645.6351375579834*blue_alt**2*diffAlt + 1.2730522155761719*blue_alt**2*cosAspect + -1.3011302947998047*blue_alt**2*sinAspect + 0.11159420013427734*blue_alt**2*cosAngleOff + -14.695868492126465*blue_alt**2*sinAngleOff + -593.7795422077179*blue_alt*diffAlt**2 + 56.97529697418213*blue_alt*diffAlt*cosAspect + 6.210783362388611*blue_alt*diffAlt*sinAspect + -11.351598918437958*blue_alt*diffAlt*cosAngleOff + 15.497141778469086*blue_alt*diffAlt*sinAngleOff + -48434722758.1483*blue_alt*cosAspect**2 + -5.246995449066162*blue_alt*cosAspect*sinAspect + -0.6854920387268066*blue_alt*cosAspect*cosAngleOff + -7.683081150054932*blue_alt*cosAspect*sinAngleOff + -48434722774.29274*blue_alt*sinAspect**2 + -1.9051815271377563*blue_alt*sinAspect*cosAngleOff + -3.2189483642578125*blue_alt*sinAspect*sinAngleOff + -48434722766.46461*blue_alt*cosAngleOff**2 + -1.359988272190094*blue_alt*cosAngleOff*sinAngleOff + -48434722765.975784*blue_alt*sinAngleOff**2 + 415.41294434666634*diffAlt**3 + 4.431054592132568*diffAlt**2*cosAspect + -8.187819063663483*diffAlt**2*sinAspect + 14.465135008096695*diffAlt**2*cosAngleOff + -7.504468888044357*diffAlt**2*sinAngleOff + -3.2432188987731934*diffAlt*cosAspect**2 + 4.548820972442627*diffAlt*cosAspect*sinAspect + -7.0754852294921875*diffAlt*cosAspect*cosAngleOff + 7.579712152481079*diffAlt*cosAspect*sinAngleOff + 12.87101697921753*diffAlt*sinAspect**2 + 1.8196303844451904*diffAlt*sinAspect*cosAngleOff + 0.8978419303894043*diffAlt*sinAspect*sinAngleOff + 6.215373992919922*diffAlt*cosAngleOff**2 + 1.5760459899902344*diffAlt*cosAngleOff*sinAngleOff + 3.4128408432006836*diffAlt*sinAngleOff**2 + 4.713005065917969*cosAspect**3 + 1.2231206893920898*cosAspect**2*sinAspect + 0.33994054794311523*cosAspect**2*cosAngleOff + 0.7669425010681152*cosAspect**2*sinAngleOff + 1.0177960395812988*cosAspect*sinAspect**2 + 0.26333045959472656*cosAspect*sinAspect*cosAngleOff + 0.23392248153686523*cosAspect*sinAspect*sinAngleOff + 1.5496840476989746*cosAspect*cosAngleOff**2 + 0.21388888359069824*cosAspect*cosAngleOff*sinAngleOff + 4.180890798568726*cosAspect*sinAngleOff**2 + -0.7129175662994385*sinAspect**3 + -0.10352802276611328*sinAspect**2*cosAngleOff + -0.5432882308959961*sinAspect**2*sinAngleOff + 0.3387293815612793*sinAspect*cosAngleOff**2 + 0.8704748153686523*sinAspect*cosAngleOff*sinAngleOff + 0.17043113708496094*sinAspect*sinAngleOff**2 + 0.19688940048217773*cosAngleOff**3 + 0.14240312576293945*cosAngleOff**2*sinAngleOff + 0.03921937942504883*cosAngleOff*sinAngleOff**2 + 0.08099126815795898*sinAngleOff**3 + 263.6614294052124*blue_alt**4 + -1512.8603755235672*blue_alt**3*diffAlt + 71.35997533798218*blue_alt**3*cosAspect + -11.264026943594217*blue_alt**3*sinAspect + 5.010807193815708*blue_alt**3*cosAngleOff + 2.270269602537155*blue_alt**3*sinAngleOff + 2210.6988503970206*blue_alt**2*diffAlt**2 + -100.11660611629486*blue_alt**2*diffAlt*cosAspect + 6.896273672580719*blue_alt**2*diffAlt*sinAspect + -2.653232842683792*blue_alt**2*diffAlt*cosAngleOff + 31.888336077332497*blue_alt**2*diffAlt*sinAngleOff + -10.444216966629028*blue_alt**2*cosAspect**2 + 10.901844412088394*blue_alt**2*cosAspect*sinAspect + -13.297839760780334*blue_alt**2*cosAspect*cosAngleOff + 16.99918720126152*blue_alt**2*cosAspect*sinAngleOff + 18.72378921508789*blue_alt**2*sinAspect**2 + 6.08647283911705*blue_alt**2*sinAspect*cosAngleOff + 22.71003770828247*blue_alt**2*sinAspect*sinAngleOff + -1.0599379539489746*blue_alt**2*cosAngleOff**2 + 2.751760333776474*blue_alt**2*cosAngleOff*sinAngleOff + 9.33937931060791*blue_alt**2*sinAngleOff**2 + -1570.4567144662142*blue_alt*diffAlt**3 + 73.54149854183197*blue_alt*diffAlt**2*cosAspect + 28.750452879816294*blue_alt*diffAlt**2*sinAspect + -11.018491446971893*blue_alt*diffAlt**2*cosAngleOff + -29.745350182056427*blue_alt*diffAlt**2*sinAngleOff + -38.879274129867554*blue_alt*diffAlt*cosAspect**2 + -7.862619407474995*blue_alt*diffAlt*cosAspect*sinAspect + 36.476838767528534*blue_alt*diffAlt*cosAspect*cosAngleOff + -27.765694469213486*blue_alt*diffAlt*cosAspect*sinAngleOff + -18.219764709472656*blue_alt*diffAlt*sinAspect**2 + -10.259405374526978*blue_alt*diffAlt*sinAspect*cosAngleOff + -25.661755979061127*blue_alt*diffAlt*sinAspect*sinAngleOff + -25.324819087982178*blue_alt*diffAlt*cosAngleOff**2 + -9.472709000110626*blue_alt*diffAlt*cosAngleOff*sinAngleOff + -31.77416229248047*blue_alt*diffAlt*sinAngleOff**2 + -5.187355041503906*blue_alt*cosAspect**3 + 1.4622862339019775*blue_alt*cosAspect**2*sinAspect + -0.2866877317428589*blue_alt*cosAspect**2*cosAngleOff + 2.5849339962005615*blue_alt*cosAspect**2*sinAngleOff + -0.42741870880126953*blue_alt*cosAspect*sinAspect**2 + -0.09732216596603394*blue_alt*cosAspect*sinAspect*cosAngleOff + 1.3953628540039062*blue_alt*cosAspect*sinAspect*sinAngleOff + -0.21757793426513672*blue_alt*cosAspect*cosAngleOff**2 + 0.4627494812011719*blue_alt*cosAspect*cosAngleOff*sinAngleOff + -5.397452354431152*blue_alt*cosAspect*sinAngleOff**2 + -0.30803269147872925*blue_alt*sinAspect**3 + 0.7261127233505249*blue_alt*sinAspect**2*cosAngleOff + 0.38739609718322754*blue_alt*sinAspect**2*sinAngleOff + 0.2718369960784912*blue_alt*sinAspect*cosAngleOff**2 + -1.2662882804870605*blue_alt*sinAspect*cosAngleOff*sinAngleOff + 0.882968544960022*blue_alt*sinAspect*sinAngleOff**2 + 0.4581758975982666*blue_alt*cosAngleOff**3 + 1.4362018406391144*blue_alt*cosAngleOff**2*sinAngleOff + -0.01850104331970215*blue_alt*cosAngleOff*sinAngleOff**2 + 1.5361876487731934*blue_alt*sinAngleOff**3 + -180.57323323190212*diffAlt**4 + -95.72139558196068*diffAlt**3*cosAspect + -11.898009572178125*diffAlt**3*sinAspect + 7.965565111488104*diffAlt**3*cosAngleOff + 14.9831523001194*diffAlt**3*sinAngleOff + -3.4810532331466675*diffAlt**2*cosAspect**2 + 1.5617841482162476*diffAlt**2*cosAspect*sinAspect + -26.71401811018586*diffAlt**2*cosAspect*cosAngleOff + 12.02545415610075*diffAlt**2*cosAspect*sinAngleOff + 6.7056725025177*diffAlt**2*sinAspect**2 + 4.024645686149597*diffAlt**2*sinAspect*cosAngleOff + 12.955219268798828*diffAlt**2*sinAspect*sinAngleOff + 1.6981469094753265*diffAlt**2*cosAngleOff**2 + 2.860257387161255*diffAlt**2*cosAngleOff*sinAngleOff + 1.5266871452331543*diffAlt**2*sinAngleOff**2 + 11.544933319091797*diffAlt*cosAspect**3 + -2.4127752482891083*diffAlt*cosAspect**2*sinAspect + 4.137317657470703*diffAlt*cosAspect**2*cosAngleOff + -2.689290761947632*diffAlt*cosAspect**2*sinAngleOff + 3.9465866088867188*diffAlt*cosAspect*sinAspect**2 + -0.3406214714050293*diffAlt*cosAspect*sinAspect*cosAngleOff + -2.323591113090515*diffAlt*cosAspect*sinAspect*sinAngleOff + 4.790468215942383*diffAlt*cosAspect*cosAngleOff**2 + -0.3382453918457031*diffAlt*cosAspect*cosAngleOff*sinAngleOff + 10.700618982315063*diffAlt*cosAspect*sinAngleOff**2 + 0.7430272698402405*diffAlt*sinAspect**3 + -1.7300704717636108*diffAlt*sinAspect**2*cosAngleOff + -0.016827702522277832*diffAlt*sinAspect**2*sinAngleOff + -0.7588976621627808*diffAlt*sinAspect*cosAngleOff**2 + 1.647592306137085*diffAlt*sinAspect*cosAngleOff*sinAngleOff + -0.9111950397491455*diffAlt*sinAspect*sinAngleOff**2 + 0.9430753588676453*diffAlt*cosAngleOff**3 + -1.469571590423584*diffAlt*cosAngleOff**2*sinAngleOff + 1.4636154174804688*diffAlt*cosAngleOff*sinAngleOff**2 + -1.2368550300598145*diffAlt*sinAngleOff**3 + 0.13893473148345947*cosAspect**4 + -0.8792426586151123*cosAspect**3*sinAspect + -0.5927371978759766*cosAspect**3*cosAngleOff + -0.5812487602233887*cosAspect**3*sinAngleOff + 3.271589756011963*cosAspect**2*sinAspect**2 + -0.10247254371643066*cosAspect**2*sinAspect*cosAngleOff + 0.2819831371307373*cosAspect**2*sinAspect*sinAngleOff + 2.7188210487365723*cosAspect**2*cosAngleOff**2 + -0.10715484619140625*cosAspect**2*cosAngleOff*sinAngleOff + 0.6903848648071289*cosAspect**2*sinAngleOff**2 + 0.23953402042388916*cosAspect*sinAspect**3 + -0.08658647537231445*cosAspect*sinAspect**2*cosAngleOff + 0.24382317066192627*cosAspect*sinAspect**2*sinAngleOff + -0.3989877700805664*cosAspect*sinAspect*cosAngleOff**2 + -2.56032133102417*cosAspect*sinAspect*cosAngleOff*sinAngleOff + -0.2419414520263672*cosAspect*sinAspect*sinAngleOff**2 + -0.4137929677963257*cosAspect*cosAngleOff**3 + -0.21618914604187012*cosAspect*cosAngleOff**2*sinAngleOff + -0.26738429069519043*cosAspect*cosAngleOff*sinAngleOff**2 + -0.12069559097290039*cosAspect*sinAngleOff**3 + 2.2547264099121094*sinAspect**4 + 0.10329008102416992*sinAspect**3*cosAngleOff + 0.25614070892333984*sinAspect**3*sinAngleOff + 2.0086026191711426*sinAspect**2*cosAngleOff**2 + 0.08739471435546875*sinAspect**2*cosAngleOff*sinAngleOff + 3.5173587799072266*sinAspect**2*sinAngleOff**2 + -0.04644203186035156*sinAspect*cosAngleOff**3 + 0.04512357711791992*sinAspect*cosAngleOff**2*sinAngleOff + 0.04626941680908203*sinAspect*cosAngleOff*sinAngleOff**2 + 0.49104785919189453*sinAspect*sinAngleOff**3 + 1.839278221130371*cosAngleOff**4 + -0.009205341339111328*cosAngleOff**3*sinAngleOff + 2.887812614440918*cosAngleOff**2*sinAngleOff**2 + -0.011905670166015625*cosAngleOff*sinAngleOff**3 + 1.3196868896484375*sinAngleOff**4"
			
	var num_allies 
	var num_enemies
	var enemies_behavior
	var agents_behavior	
		
	var agents_config = { "blue_agents": 
			{                        
				"init_position": {"x": 0.0, "y": 25000.0,"z": 30.0},
				"offset_pos": {	"x": 0.0, "y": 0.0, "z": 0.0},
				"init_hdg": 0.0,                        
				"target_position": {"x": 0.0,"y": 25000.0,"z": 30.0},
				"rnd_offset_range":{"x": 10.0,"y": 10000.0,"z": 5.0},
				#"rnd_offset_range":{"x": 0.0,"y": 0.0,"z": 0.0},
				"rnd_shot_dist_var": 0.0,
				"rmax_model" : DEFAULT_RMAX_MODEL, 																						
				"rnez_model" : DEFAULT_RNEZ_MODEL
			},
		
			"red_agents":
			{ 
				"init_position": {"x": 0.0,"y": 25000.0,"z": -30.0},
				"offset_pos": {"x": 0.0,"y": 0.0,"z": 0.0},
				"init_hdg" : 180.0,                        
				"target_position": {"x": 0.0,"y": 25000.0,"z": 30.0},
				"rnd_offset_range":{"x": 10.0,"y": 10000.0,"z": 5.0},
				#"rnd_offset_range":{"x": 0.0,"y": 0.0,"z": 0.0},
				"rnd_shot_dist_var": 0.0,
				"rmax_model" : DEFAULT_RMAX_MODEL, 																						
				"rnez_model" : DEFAULT_RNEZ_MODEL					
		}
	}
			
	func _init(config):				
						
		self.num_allies 		= config.get("num_allies", DEFAULT_NUM_ALLIES)
		self.num_enemies 		= config.get("num_enemies", DEFAULT_NUM_ENEMIES)
		self.enemies_behavior 	= config.get("enemies_behavior", DEFAULT_ENEMIES_BEHAVIOR)
		self.agents_behavior 	= config.get("agents_behavior", DEFAULT_AGENTS_BEHAVIOR)
		self.agents_config 		= config.get("agents_config" , self.agents_config)
				
class SimGroups:
	
	var BLUE
	var RED
	var FIGHTER
	var AGENT
	var ENEMY
	var MISSILE
	
	func _init(sim_id):
		BLUE     = "BLUE"       + str(sim_id)
		RED      = "RED"        + str(sim_id)
		FIGHTER  = "FIGHTER_"   + str(sim_id)
		AGENT    = "AGENT_"     + str(sim_id)
		ENEMY    = "ENEMIE_"    + str(sim_id)
		MISSILE  = "MISSILE_"   + str(sim_id)

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
	var vert_aspect_angle
	var aspect_angle
	var angle_off
	var inv_aspect_angle
	var inv_angle_off
	var vert_aspect_angleR
	var aspect_angleR
	var angle_offR
	var inv_aspect_angleR
	var inv_angle_offR
	var last_know_pos
	var last_detection
	var radar_range
	var radar_hfov
	var radar_vfov
	var last_track_hdg
	var detected
	var just_detected
	var just_lost
	var is_alive	
	var is_missile_support
	var own_missile_RMax
	var own_missile_Nez
	var enemy_missile_RMax
	var enemy_missile_Nez	
	var threat_factor
	var offensive_factor
	
	func _init(_id, fighter, track_obj):
		id = _id		
		obj = track_obj
		last_know_pos = fighter.global_transform.origin
		last_track_hdg = 0.0
		last_detection = -500.0 #dead at the beginning
		is_alive = false
		is_missile_support = false
		radar_range= fighter.radar_range
		radar_hfov = fighter.radar_hfov
		radar_vfov = fighter.radar_vfov
		
		update_track(fighter, track_obj, 0.0)
					
	
	func is_track_detectable() -> bool:
			
		if dist > radar_range:
			return false
		
		if aspect_angle < radar_hfov[0] or aspect_angle > radar_hfov[1]:
			return false
		if vert_aspect_angle < radar_vfov[0] or vert_aspect_angle > radar_vfov[1]:
			return false
		return true
	
	func update_track(fighter, track_obj, time_detected):
								
		dist 			  = fighter.global_transform.origin.distance_to(track_obj.global_transform.origin)
		radial			  = Calc.get_hdg_2d(fighter.global_transform.origin, track_obj.global_transform.origin)
		
		vert_aspect_angle 	= Calc.get_vertical_aspect_angle(fighter, track_obj)
		angle_off 		  	= Calc.get_2d_angle_off(fighter.current_hdg, track_obj.current_hdg )
		aspect_angle 	  	= Calc.get_2d_aspect_angle(fighter.current_hdg, radial)
		
		inv_angle_off 	  	= -angle_off
		inv_aspect_angle	= Calc.get_2d_aspect_angle(track_obj.current_hdg, radial - 180)
		
		#print(fighter.id, ":ASPECT: ", aspect_angle, " AOff: ", angle_off, " Rad: ", radial, " HDG: ", fighter.current_hdg)
		#print(fighter.id, ":invASPECT: ", inv_aspect_angle, " InvAOff: ", inv_angle_off)
				
		vert_aspect_angleR	= deg_to_rad(vert_aspect_angle)
		angle_offR 		  	= deg_to_rad(angle_off)
		aspect_angleR 	  	= deg_to_rad(aspect_angle)
		inv_angle_offR 	  	= deg_to_rad(inv_angle_off)
		inv_aspect_angleR	= deg_to_rad(inv_aspect_angle)
				
		var is_detectable = is_track_detectable()		
				
		if is_detectable:
			#print(" detectable:", [angle_off,
			#						aspect_angle,
			#						vert_aspect_angle])
			last_know_pos = track_obj.global_transform.origin
			last_track_hdg = track_obj.current_hdg 
			last_detection = time_detected
			is_alive = true
			if not detected:
				just_detected = true			
				detected = true
		else:
			if time_detected - last_detection > 20.0:
				is_alive = false
			
			if detected:
				just_lost = true			
				detected = false
		
	
	func update_wez_data(wez_ranges):
		
		own_missile_RMax 	= wez_ranges[0] * SConv.NM2GDM
		own_missile_Nez		= wez_ranges[1] * SConv.NM2GDM
		enemy_missile_RMax	= wez_ranges[2] * SConv.NM2GDM
		enemy_missile_Nez	= wez_ranges[3] * SConv.NM2GDM
						
		if dist <= own_missile_RMax:
			if dist > own_missile_Nez and own_missile_Nez != own_missile_RMax:				
				offensive_factor = 1.0 - 0.5 * (dist - own_missile_Nez) / (own_missile_RMax - own_missile_Nez)
			else:			
				offensive_factor = min(own_missile_Nez / dist, 2.0)
		else:
			offensive_factor = 0.5 * exp(-2.0 * ((dist - own_missile_RMax)/own_missile_RMax))
			#threat_factor = 0.5 * own_missile_RMax / dist
					
		if dist <= enemy_missile_RMax:
			if dist > enemy_missile_Nez and enemy_missile_Nez != enemy_missile_RMax:				
				threat_factor = 1.0 - 0.5 * (dist - enemy_missile_Nez) / (enemy_missile_RMax - enemy_missile_Nez)
			else:			
				threat_factor = min(enemy_missile_Nez / dist, 2.0)
		else:
			threat_factor = 0.5 * exp(-2.0 * ((dist- enemy_missile_RMax)/enemy_missile_RMax))
			#threat_factor = 0.5 * own_missile_RMax / dist
		if offensive_factor > 2:
			print([own_missile_RMax, own_missile_Nez, enemy_missile_RMax, enemy_missile_Nez], [dist])
			print("Factors:", [offensive_factor, threat_factor])
		
	func detected_status(_detected):
		self.detected = _detected
		
	func radial2aspect_angle(own_hdg, taget_radial):		
		return clamp_hdg(taget_radial - own_hdg)
		
	func clamp_hdg(hdg):
		if hdg > 180.0:
			return hdg - 360.0
		elif hdg < -180.0:
			return hdg + 360.0
		else:
			return hdg
		
class RewardsControl:
		
	var printRewards = false
	
	var mission = 0.0
	var missile_fire = 0.0
	var missile_miss = 0.0
	var detect_loss = 0.0
	var keep_track = 0.0
	var hit_enemy = 0.0
	var hit_own = 0.0
	var final_reward = 0.0
	
	var mission_factor
	var missile_fire_factor
	var missile_no_fire_factor
	var missile_miss_factor
	var detect_loss_factor
	var keep_track_factor
	var hit_enemy_factor
	var hit_own_factor
	var situation_factor
	
	var final_team_killed_factor
	var final_enemy_on_target_factor
	var final_enemies_killed_factor
	var final_max_cycles_factor
	
	var Owner = null
	
	
	func _init(	_owner,
				_mission_factor = 1.0,
			 	_missile_fire_factor = -0.1,
				_missile_no_fire_factor = -0.001,
				_missile_miss_factor = -0.5,
				_detect_loss_factor = -0.1,
				_keep_track = 0.001,
				_hit_enemy_factor = 3.0,
				_hit_own_factor = -5.0,
				_situation_factor = 0.1, 
				_final_team_killed_factor = -5.0,
				_final_enemy_on_target_factor = -3.0,
				_final_enemies_killed_factor = 5.0,
				_final_max_cycles_factor = 3.0):
					
		Owner = _owner
		mission_factor = _mission_factor
		missile_fire_factor = _missile_fire_factor
		missile_no_fire_factor = _missile_no_fire_factor
		missile_miss_factor = _missile_miss_factor
		detect_loss_factor = _detect_loss_factor
		keep_track_factor = _keep_track 
		hit_enemy_factor = _hit_enemy_factor
		hit_own_factor = _hit_own_factor
		situation_factor = _situation_factor 
		
		final_team_killed_factor = _final_team_killed_factor
		final_enemy_on_target_factor = _final_enemy_on_target_factor
		final_enemies_killed_factor = _final_enemies_killed_factor
		final_max_cycles_factor = _final_max_cycles_factor
	
	func add_mission_rew(ref_value):
		mission += mission_factor * ref_value
		if printRewards:
			print("Figther::" , Owner.get_meta("id" ), "::Info::Mission Rewards -> ", mission )
	
	func add_missile_fire_rew():
		missile_fire += missile_fire_factor
		if printRewards:
			print("Figther::Info::missile_fire Rewards -> ", missile_fire )
	
	func add_missile_no_fire_rew():
		missile_fire += missile_no_fire_factor
		if printRewards:			
			print("Figther::Info::missile_fire Rewards -> ", missile_fire )
	
	func add_missile_miss_rew():
		missile_miss += missile_miss_factor
		if printRewards:
			print("Figther::Info::missile_miss Rewards -> ", missile_miss )
	
	func add_detect_loss_rew(multiplier = 1.0):
		detect_loss += detect_loss_factor * multiplier
		if printRewards:
			print("Figther::", Owner.get_meta("id" ), "::Info::detect_loss Rewards -> ", detect_loss )
	
	func add_keep_track_rew():
		keep_track += keep_track_factor
		if printRewards:
			print("Figther::", Owner.get_meta("id" ), "::Info::keep_track Rewards -> ", keep_track )
					
	func add_hit_enemy_rew():
		hit_enemy += hit_enemy_factor				
	
	func add_hit_own_rew():
		hit_own += hit_own_factor
		#print("Figther::" , Owner.get_meta("id"), "::Info::hit_own Rewards -> ", hit_own )
		
	func get_total_rewards_and_reset():
		var total_rewards = mission + missile_fire + missile_miss + \
							detect_loss + hit_enemy + hit_own + final_reward
		
		if printRewards:
			print("Figther::Info::Total Rewards -> ", total_rewards )
		# Reset the values
		mission = 0.0
		missile_fire = 0.0
		missile_miss = 0.0
		detect_loss = 0.0
		keep_track = 0
		hit_enemy = 0.0
		hit_own = 0.0		
		final_reward = 0.0
				
		return total_rewards
	
	func add_final_episode_reward(condition):
						
		if condition == "Enemy_Achieved_Target":
			final_reward += final_enemy_on_target_factor			
			#print("Figther::Info::Enemies_On Target Rewards -> ", final_reward )			
		elif condition == "Enemies_Killed":
			final_reward += final_enemies_killed_factor  + final_max_cycles_factor
			#print("Figther::Info::Enemies_Killed Rewards -> ", final_reward )			
		elif condition == "Team_Killed":
			final_reward += final_team_killed_factor + final_enemy_on_target_factor
			#print("Figther::Info::TEAM_Killed Rewards -> ", final_reward )			
		elif condition == "Max_Cycles":
			final_reward += final_reward
			#print("Figther::Info::Rewards Added Max_Cycles -> ", final_reward )
		else:
			print("Figther::Warning Trying to add unknow final reward (", condition , ")")			

class FinalState:
	var blues_killed = 0
	var reds_killed = 0
	var blue_target = 0
	var red_taget = 0
	
	func _init():
		pass
	
	func reset():
		blues_killed = 0
		reds_killed  = 0
		blue_target  = 0
		red_taget    = 0
		
	

	
	

