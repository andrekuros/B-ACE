from godot_rl.core.godot_env import GodotEnv
from pettingzoo.utils import ParallelEnv
import numpy as np
import gymnasium as gym


class GodotRLPettingZooWrapper(GodotEnv):
    metadata = {'render.modes': [], 'name': "godot_rl_multi_agent"}

    def __init__(self, env_path, num_agents, **kwargs):
        
        super().__init__(env_path=env_path, **kwargs)

        # self.num_agents = num_agents
        self.agents = [f'agent_{i}' for i in range(num_agents)]  # Initialize agents
        self.possible_agents = self.agents[:]
        
        # Initialize observation and action spaces for each agent
        # This should be adapted based on the specific structure of your Godot environment
        self.observation_spaces = {agent: self.observation_space for agent in self.agents}
        self.action_spaces = {agent: self.action_space for agent in self.agents}
        
        self._cumulative_rewards = {agent : 0  for agent in self.possible_agents}                
        self.rewards =  {agent : 0  for agent in self.possible_agents}
        self.terminations =  {agent : False  for agent in self.possible_agents}
        self.truncations =  {agent : False  for agent in self.possible_agents} 
        self.observations =  {agent : {}  for agent in self.possible_agents}  
        self.info =  {agent : {}  for agent in self.possible_agents}  



    # def reset(
    #         self,
    #         seed: int | None = None,
    #         options: dict | None = None,
    #     ) -> tuple[dict[AgentID, ObsType], dict[AgentID, dict]]:
            
    #         obs, _ super().reset(self, )"""Resets the environment.

    #         And returns a dictionary of observations (keyed by the agent name)
    #         """
    #         raise NotImplementedError
    # def reset(self):
    #     self.observations  = super().reset()
    #     # Assuming the reset method returns a dictionary of observations for each agent
    #     return self.observations
    
    # @property
    # def observation_space(self, agent):
    #     return self.observation_spaces[agent] 
    
    # @property
    # def action_space(self, agent):
    #     return self.action_spaces[agent]

    # def step(self, actions):
    #     # Assuming the environment's step function can handle a dictionary of actions for each agent
    #     observations, rewards, dones, infos = super().step(actions)
        
    #     # Update the list of active agents based on the 'dones' information
    #     for agent, done in dones.items():
    #         if done:
    #             self.agents.remove(agent)

    #     return observations, rewards, dones, infos
    
    def last(self, env=None):
    
        """Return the last observations, rewards, and done status."""                        
        return (
            self.observations,
            self.rewards,
            self.terminations,
            self.truncations,
            self.info,
        )
        

    