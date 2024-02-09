from godot_rl.core.godot_env import GodotEnv
from pettingzoo.utils import ParallelEnv
import numpy as np

class GodotRLPettingZooWrapper(ParallelEnv):
    metadata = {'render.modes': [], 'name': "godot_rl_multi_agent"}

    def __init__(self, env_path, num_agents, **kwargs):
        super().__init__()
        self.env = GodotEnv(env_path=env_path, **kwargs)
        self.num_agents = num_agents
        self.agents = [f'agent_{i}' for i in range(self.num_agents)]  # Initialize agents
        self.possible_agents = self.agents[:]
        
        # Initialize observation and action spaces for each agent
        # This should be adapted based on the specific structure of your Godot environment
        self.observation_spaces = {agent: self.env.observation_space for agent in self.agents}
        self.action_spaces = {agent: self.env.action_space for agent in self.agents}

    def reset(self):
        observations = self.env.reset()
        # Assuming the reset method returns a dictionary of observations for each agent
        return observations

    def step(self, actions):
        # Assuming the environment's step function can handle a dictionary of actions for each agent
        observations, rewards, dones, infos = self.env.step(actions)
        
        # Update the list of active agents based on the 'dones' information
        for agent, done in dones.items():
            if done:
                self.agents.remove(agent)

        return observations, rewards, dones, infos

    def close(self):
        self.env.close()
