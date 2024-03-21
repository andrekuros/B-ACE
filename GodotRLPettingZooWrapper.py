from godot_rl.core.godot_env import GodotEnv
from pettingzoo.utils import ParallelEnv

from godot_rl.core.utils import ActionSpaceProcessor, convert_macos_path
import numpy as np
import gymnasium as gym
import torch
import atexit
from sys import platform
from gymnasium import spaces
import json
import subprocess
from typing import Optional
import random


class GodotRLPettingZooWrapper(GodotEnv, ParallelEnv):
    metadata = {'render.modes': [], 'name': "godot_rl_multi_agent"}

    def __init__(self,
                env_path: str = None,
                port: int = GodotEnv.DEFAULT_PORT,
                show_window: bool = True,
                seed: int = 0,
                framerate: Optional[int] = None,
                action_repeat: Optional[int] = None,
                speedup: Optional[int] = None,
                convert_action_space: bool = False,
                device: str = "cpu",
                **env_config_kwargs):                       
        #super().__init__( **kwargs)    
        
        self.device = device        
        self.seed = env_config_kwargs.pop("seed", 0)                
        self.action_repeat = env_config_kwargs.pop("action_repeat", 20)                    
        self.num_allies = env_config_kwargs.pop("num_allies", 1)
        self.num_enemies = env_config_kwargs.pop("num_enemies", 1)
        self.action_type = env_config_kwargs.pop("action_type", "Low_Level_Continuous")
        self.enemies_baseline = env_config_kwargs.pop("enemies_baseline", "baseline1")
        self.full_observation = env_config_kwargs.pop("full_observation", 0)
        self.actions_2d = env_config_kwargs.pop("actions_2d", 0)      
                        
        port = GodotRLPettingZooWrapper.DEFAULT_PORT + random.randint(0,3100) 
        self.port = port
        self.proc = None
        if env_path is not None and env_path != "debug":
            env_path = self._set_platform_suffix(env_path)

            self.check_platform(env_path)  

            self._launch_env(env_path, port, show_window, framerate, self.seed, action_repeat, speedup)
        else:
            print("No game binary has been provided, please press PLAY in the Godot editor")
        
        self.connection = self._start_server()
        self.num_envs = None
        self._handshake()
        self._get_env_info()
        # sf2 requires a tuple action space
        self._tuple_action_space = spaces.Tuple([v for _, v in self._action_space.items()])
        self.action_space_processor = ActionSpaceProcessor(self._tuple_action_space, convert_action_space)

        atexit.register(self._close)
                                
        #Initialization for PettingZoo Paralell
        
        self.agents = [f'agent_{i}' for i in range(self.num_allies)]  # Initialize agents
        self.possible_agents = self.agents[:]

        self.agent_idx = [ {agent : i} for i, agent in enumerate(self.possible_agents)]                 
        # Initialize observation and action spaces for each agent
        self.observation_spaces = {agent: self.observation_space['obs'] for agent in self.agents}
        self.action_spaces = {agent: self.action_space for agent in self.agents}

        self.observation_space = self._observation_space
        
        self._cumulative_rewards = {agent : 0  for agent in self.possible_agents}                
        self.rewards =  {agent : 0  for agent in self.possible_agents}
        self.terminations =  {agent : False  for agent in self.possible_agents}
        self.truncations =  {agent : False  for agent in self.possible_agents} 
        self.observations =  {agent : {}  for agent in self.possible_agents}  
        self.info =  {agent : {}  for agent in self.possible_agents}  


    def _launch_env(self, env_path, port, show_window, framerate, seed, action_repeat, speedup): 
                                                                           
        # --fixed-fps {framerate}
        path = convert_macos_path(env_path) if platform == "darwin" else env_path

        launch_cmd = f"{path} --port={port} --env_seed={seed}"

        # Building the launch command
        launch_cmd = f"{env_path}"
        
        if not show_window:
            launch_cmd += " --disable-render-loop --headless"
        if seed is not None:
            launch_cmd += f" --seed={seed}"
        if port is not None:
            launch_cmd += f" --port={port}"
        if framerate is not None:
            launch_cmd += f" --fixed-fps {framerate}"
        launch_cmd += f" --speedup={speedup}"
        launch_cmd += f" --action_repeat={action_repeat}"
        
        launch_cmd += f" --num_allies={self.num_allies}"
        launch_cmd += f" --num_enemies={self.num_enemies}"
        launch_cmd += f" --action_type={self.action_type}"
        launch_cmd += f" --enemies_baseline={self.enemies_baseline}"
        launch_cmd += f" --full_observation={self.full_observation}"
        launch_cmd += f" --actions_2d={self.actions_2d}"                

        launch_cmd = launch_cmd.split(" ")
        self.proc = subprocess.Popen(
            launch_cmd,
            start_new_session=True,
            # shell=True,
        )
    
    def reset(self, seed=0, options = None):
        
        result  = super().reset()
        
        observations = []
        self.observations = {}

        for i, indiv_obs in enumerate(result[0]):
            
            self.observations[self.possible_agents[i]] =  indiv_obs["obs"] 
            self.info[self.possible_agents[i]] = {}                  
        # Assuming the reset method returns a dictionary of observations for each agent        
        return self.observations, self.info  
    
    def _observation_space(self, agent):        
        return self.observation_spaces[agent]
    def action_space(self, agent = None):
        
        return self.action_space_processor.action_space
    
    
    def step(self, actions):
        # Assuming the environment's step function can handle a dictionary of actions for each agent                                      
        if self.action_type == "Low_Level_Continuous":
            godot_actions = [np.array([action]) for agent, action in actions.items()]        
        elif self.action_type == "Low_Level_Discrete": 
            godot_actions = [ self.decode_action(action) for agent, action in actions.items()]
        else:
            print("GododtPZWrapper::Error:: Unknow Actions Type -> ", self.actions_type)
                                
        obs, reward, dones, truncs, info = super().step(godot_actions, order_ij=True)
        
        # Assuming 'obs' is a list of dictionaries with 'obs' keys among others
        for i, agent in enumerate(self.possible_agents):
            # Convert observations, rewards, etc., to tensors
            # if dones[i] == True:
            #     continue
            # .to('cuda') moves the tensor to GPU if you're using CUDA; remove it if not using GPU
            self.observations[agent] =  obs[i]['obs']            
            self.rewards[agent] = reward[i],#torch.tensor([reward[i]], dtype=torch.float32).to('cuda')
            self.terminations[agent] = dones[i],#torch.tensor([False], dtype=torch.bool).to('cuda')  # Assuming False for all
            self.truncations[agent] = truncs[i],#torch.tensor([False], dtype=torch.bool).to('cuda')  # Assuming False for all
            # For 'info', it might not need to be a tensor depending on its use
            self.info[agent] = info[i]  # Assuming 'info' does not need tensor conversion
            
            #print( self.observations[agent])
            
        #  # Update the list of active agents based on the 'dones' information
        #  for agent, done in dones.items():
        #      if done:
        #          self.agents.remove(agent)


        return self.observations, self.rewards, self.terminations, self.truncations, self.info 
    
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


    