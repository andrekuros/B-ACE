from .godot_env import GodotEnv
from pettingzoo.utils import ParallelEnv

from .utils import ActionSpaceProcessor, convert_macos_path
import numpy as np
import atexit
from sys import platform
from gymnasium import spaces
import random


class B_ACE_GodotPettingZooWrapper(GodotEnv, ParallelEnv):
    metadata = {'render.modes': [], 'name': "godot_rl_multi_agent"}

    def __init__(self,
                env_path: str = None,                
                seed: int = 0,         
                convert_action_space: bool = False,
                device: str = "cpu",
                **config_kwargs):                               
        
        self.device = device
        
        self.env_config = config_kwargs.get("EnvConfig", "")     
        #Godot Line Parameters Commands
        self.env_path       = self.env_config.get("env_path", "./bin/BVR.exe")  
        self.show_window    = int(self.env_config.get("renderize", 1))  
        self._seed          = int(self.env_config.get("seed", 1))  
        self.action_repeat  = int(self.env_config.get("action_repeat", 20))  
        self.action_type    = self.env_config.get("action_type", "Low_Level_Continuous")  
        self.speedup        = int(self.env_config.get("speed_up", 1000))                          
        self.parallel_envs  = int(self.env_config.get("parallel_envs", 1))          
        
        self.agents_config = config_kwargs.get("AgentsConfig", "")
        self._num_agents = int(self.agents_config["blue_agents"].get("num_agents", 1))
        
        self.share_states  = int(self.agents_config["blue_agents"].get("share_states", 1))
        self.share_tracks =  int(self.agents_config["blue_agents"].get("share_tracks", 1))       
        
        self.additional_config = self.env_config.get("additional_config", "") 
        
        self.port = B_ACE_GodotPettingZooWrapper.DEFAULT_PORT + random.randint(0,3100)                 
        self.proc = None
        
        if self.env_path is not None and self.env_path != "debug":
            self.env_path = self._set_platform_suffix(self.env_path)

            self.check_platform(self.env_path)  

            self._launch_env(self.env_path, self.port, self.show_window == 1, None, self._seed, self.action_repeat, self.speedup)
        else:
            print("No game binary has been provided, please press PLAY in the Godot editor")
        
        self.host_binding = config_kwargs.get("host_binding", False)
        self.connection = self._start_server()
        self.num_envs = None
        
        self._handshake()           
        
        self.action_spaces = []
        self.observation_spaces = []     
        self.send_sim_config(self.env_config, self.agents_config)                
        
        self.action_spaces = []
        self.observation_spaces = []

        env_info = self._get_env_info()          
                
        self.observation_labels = env_info["observation_labels"]
                
        self.tuple_action_spaces = [
            spaces.Tuple([v for _, v in action_space.items()]) for action_space in self.action_spaces
        ]
        # Single agent action space processor using the action space(s) of the first agent
        self.action_space_processor = ActionSpaceProcessor(self.tuple_action_spaces[0], convert_action_space)
                
        # For multi-policy envs: The name of each agent's policy set in the env itself (any training_mode
        # AIController instance is treated as an agent)
        self.agent_policy_names

        atexit.register(self._close)
                                
        #Initialization for PettingZoo Paralell
        self.agents = [f'agent_{i}' for i in range(self._num_agents)]  # Initialize agents
        self.possible_agents = self.agents[:]
        
                        
        self.obs_map= {agent : {label: index for index, label in enumerate(self.observation_labels[str(101 + i)])}  for i,agent in enumerate(self.possible_agents)}               

        self.agent_idx = [ {agent : i} for i, agent in enumerate(self.possible_agents)]                 
        
        self.observation_space = self.observation_spaces[0]["obs"]
        self.action_space = self.action_spaces[0]["input"]
        
        self._cumulative_rewards = {agent : 0  for agent in self.possible_agents}                
        self.rewards =  {agent : 0  for agent in self.possible_agents}
        self.terminations =  {agent : False  for agent in self.possible_agents}
        self.truncations =  {agent : False  for agent in self.possible_agents} 
        self.observations =  {agent : []  for agent in self.possible_agents}  
        self.info =  {agent : []  for agent in self.possible_agents}  
        self.infos =  {agent : []  for agent in self.possible_agents}  
                            
    def send_sim_config(self, _env_config, _agents_config):
        message = {"type": "config"}        
        message["agents_config"] = _agents_config
        message["env_config"] = _env_config
        self._send_as_json(message)
            
        
    def reset(self, seed=0, options = None):
        
        result  = super().reset()
    
        self.observations = {}          
        
        for i, indiv_obs in enumerate(result[0]):
                        
            self.observations[self.possible_agents[i]] = {"obs": indiv_obs["obs"], "mask": [True for _ in range(4)]}
            #self.observations[self.possible_agents[i]] =  indiv_obs["obs"] 
            self.info[self.possible_agents[i]] = {self.possible_agents[i]}                  
        # Assuming the reset method returns a dictionary of observations for each agent        
                
        return self.observations, self.info  
    
    
    def _observation_space(self, agent):        
        return self.observation_spaces[agent]
    
    def action_space(self, agent = None):        
        return self.action_space_processor.action_space
    
    def seed(self, _seed):
        self.seed = _seed
    
    def step(self, actions, order_ij=True):
                
        # Assuming the environment's step function can handle a dictionary of actions for each agent                                      
        if self.action_type == "Low_Level_Continuous":            
            godot_actions = np.array([np.array([action]) for agent, action in actions.items()])  
                   
        elif self.action_type == "Low_Level_Discrete": 
            godot_actions = [ self.decode_action(action) for agent, action in actions.items()]            
        else:
            print("GododtPZWrapper::Error:: Unknow Actions Type -> ", self.actions_type) 
               
        self.rewards = 0                               
        obs, reward, dones, truncs, info = super().step(godot_actions, order_ij=order_ij)
        
      
                
        self.observations = {agent_name : {"obs": _obs["obs"], "mask": [True for _ in range(4)]} for agent_name, _obs in obs.items()}
        
        self.terminations = False
        self.truncations = False        
        self.rewards = 0.0
        
        for i, agent in enumerate(self.possible_agents):
            
            self.terminations = self.terminations or dones[agent]
            self.truncations = self.truncations and truncs[agent]           
                        
            self.rewards += reward[agent]   
            
        return self.observations, self.rewards, self.terminations, self.truncations, self.info 
    
    def _process_obs(self, response_obs):
        return response_obs
    
    def last(self, env=None):
        
        """Return the last observations, rewards, and done status."""                        
        return (
            self.observations,
            self.rewards,
            self.terminations,
            self.truncations,
            self.info,
        )
                
    def decode_action(self, encoded_action):
        # Decode back to the original action tuple        
        turn_input = encoded_action % 5
        level_input = (encoded_action // 5.0) % 5
        fire_input = (encoded_action // 25.0) % 2
        return np.array([fire_input, level_input, turn_input])
