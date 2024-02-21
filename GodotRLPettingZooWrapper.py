from godot_rl.core.godot_env import GodotEnv
from pettingzoo.utils import ParallelEnv
import numpy as np
import gymnasium as gym
import torch


class GodotRLPettingZooWrapper(GodotEnv, ParallelEnv):
    metadata = {'render.modes': [], 'name': "godot_rl_multi_agent"}

    def __init__(self, num_agents = 2, **kwargs):
                
        super().__init__( **kwargs)

        # self.num_agents = num_agents
        self.agents = [f'agent_{i}' for i in range(num_agents)]  # Initialize agents
        self.possible_agents = self.agents[:]
        
        self.agent_idx = [ {agent : i} for i, agent in enumerate(self.possible_agents)]
                
        # Initialize observation and action spaces for each agent
        self.observation_spaces = {agent: self._observation_space['observation'] for agent in self.agents}
        self.action_spaces = {agent: self.action_space for agent in self.agents}
        
        # self.observation_space = self._observation_space
        # self.action_space = self._action_space
        
        self._cumulative_rewards = {agent : 0  for agent in self.possible_agents}                
        self.rewards =  {agent : 0  for agent in self.possible_agents}
        self.terminations =  {agent : False  for agent in self.possible_agents}
        self.truncations =  {agent : False  for agent in self.possible_agents} 
        self.observations =  {agent : {}  for agent in self.possible_agents}  
        self.info =  {agent : {}  for agent in self.possible_agents}  

    
    def reset(self, seed=0, options = None):
        
        result  = super().reset()
        
        observations = []
        self.observations = {}

        for i, indiv_obs in enumerate(result[0]):
            # self.observations[self.possible_agents[i]] = { "observation" : torch.tensor(indiv_obs['obs']).to('cuda') }
            # self.observations[self.possible_agents[i]] = np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]).astype(np.float32)#np.array(indiv_obs['observation']).astype(np.float32)
            self.observations[self.possible_agents[i]] =  indiv_obs["observation"] 
            # observations.append(indiv_obs['observation'])
            self.info[self.possible_agents[i]] = {}
            
        # observations =   {'agent_0':  np.array([ 0.        ,  0.        ,  0.52255476,  0.8312247 , -1.4231853 ,
        # -0.4940913 , -1.1777982 , -0.00508968, -0.22760977,  0.10361672,
        # -0.4955089 , -0.27061597,  0.4041192 , -0.00955313,  0.   ]).astype(np.float32), 'agent_1':  np.array([ 0.        ,  0.        ,  0.02704582,  0.5606087 , -0.92767644,
        # -0.22347532, -0.68228924,  0.2655263 ,  0.26789916,  0.37423268,  0.        ,      0.        ,  0.        ,  0.        ]).astype(np.float32)}
        # # self.observations =  {agent :  { }  for agent in self.possible_agents}  
               
        
        # Assuming the reset method returns a dictionary of observations for each agent
        return self.observations, self.info
    
    def observation_space(self, agent):
         return self.observation_spaces[agent]
  
    # def _action_space(self, agent=None):
    #      if agent == None:
    #          return self.action_spaces.values()[0]
    #      return self.action_spaces[agent]


    def action_space(self, agent = None):
        
        return self.action_space_processor.action_space
    
    
    
    def step(self, actions):
        # Assuming the environment's step function can handle a dictionary of actions for each agent
                       
       
        godot_actions = [np.array([action]) for agent, action in actions.items()]
                
        obs, reward, dones, truncs, info = super().step(godot_actions, order_ij=True)
        
        # Assuming 'obs' is a list of dictionaries with 'obs' keys among others
        for i, agent in enumerate(self.possible_agents):
            # Convert observations, rewards, etc., to tensors
            # .to('cuda') moves the tensor to GPU if you're using CUDA; remove it if not using GPU
            self.observations[agent] =  obs[i]['observation']
            # self.observations[agent] = {torch.tensor(obs[i]['obs'], dtype=torch.float32).to('cuda')}
            self.rewards[agent] = reward[i],#torch.tensor([reward[i]], dtype=torch.float32).to('cuda')
            self.terminations[agent] = dones[i],#torch.tensor([False], dtype=torch.bool).to('cuda')  # Assuming False for all
            self.truncations[agent] = truncs[i],#torch.tensor([False], dtype=torch.bool).to('cuda')  # Assuming False for all
            # For 'info', it might not need to be a tensor depending on its use
            self.info[agent] = info[i]  # Assuming 'info' does not need tensor conversion

        #  # Update the list of active agents based on the 'dones' information
        #  for agent, done in dones.items():
        #      if done:
        #          self.agents.remove(agent)

        # print(self.rewards, dones)
        # print(self.observations)
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
                

    